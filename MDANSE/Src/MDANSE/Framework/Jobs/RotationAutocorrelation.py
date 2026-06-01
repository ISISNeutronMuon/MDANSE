#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import numpy as np
from scipy.signal import correlate
from scipy.spatial.transform import Rotation

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    CorrelationWindow,
    DynamicSingleChoice,
    FrameSelect,
    MDANSETrajectory,
    OutputFile,
    RunningMode,
)
from MDANSE.Mathematics.Geometry import center_of_mass


class RotationAutocorrelation(IJob):
    """Calculates the rotation angle correlation of molecules.

    For each molecule, the Kabsch algorithm is used to determine the
    rotation angles relative to the original position at each time step.

    """

    enabled = False

    label = "Rotation Autocorrelation"

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    molecule_name = DynamicSingleChoice(
        choices="chemical_system._clusters.keys()", depends={"choices": "trajectory"}
    )
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        molecules = self.trajectory.chemical_system._clusters[self.molecule_name]

        self._indices = set(self.trajectory.atom_indices)

        self.valid_molecules = [
            mol for mol in molecules if self._indices.issuperset(mol)
        ]

        self.numberOfSteps = len(self.valid_molecules)

        self.masses = np.array(
            self.trajectory.chemical_system.atom_property(
                "atomic_weight",
            ),
        )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.frames.times,
            units="ps",
        )

        self._outputData.add(
            "frame",
            "LineOutputVariable",
            np.arange(len(self.frames)),
            units="ps",
        )

        self._outputData.add(
            "axis_index",
            "LineOutputVariable",
            np.arange(
                self.trajectory.chemical_system.number_of_molecules(
                    self.molecule_name,
                ),
            ),
            units="au",
        )

        for axis in "xyz":
            self._outputData.add(
                f"rotation_around_{axis}",
                "LineOutputVariable",
                (len(self.frames),),
                axis="frame",
                units="au",
            )
            self._outputData.add(
                f"{axis}_rotation_ac",
                "LineOutputVariable",
                (len(self.frames),),
                axis="time",
                units="au",
                main_result=True,
            )

    def run_step(self, index: int) -> tuple[int, np.ndarray]:
        """Run the analysis for a single molecule.

        Parameters
        ----------
        index : int
            Index of the molecule in the chemical system.

        Returns
        -------
        tuple[int, np.ndarray]
            Molecule index and the correlation array.

        """
        molecule = self.valid_molecules[index]
        masses = self.masses[molecule]

        euler_angles = np.empty((len(self.frames), 3))
        ref_coords = None

        for i, frame_index in enumerate(self.frames):
            configuration = self.trajectory.configuration(
                frame_index,
            )
            coordinates = configuration.contiguous_configuration().coordinates[molecule]
            current_coords = coordinates - center_of_mass(coordinates, masses)
            if i == 0:
                ref_coords = current_coords
                euler_angles[i] = 0.0
            else:
                rotation = Rotation.align_vectors(current_coords, ref_coords)[0]
                euler_angles[i] = rotation.as_euler("xyz", degrees=True)

        n_configs = self.frame_window
        ac = [
            correlate(
                euler_angles[:, ax_ind], euler_angles[:n_configs, ax_ind], mode="valid"
            )
            / n_configs
            for ax_ind in range(3)
        ]
        return index, (ac, euler_angles)

    def combine(self, index: int, x: np.ndarray):
        """Add the partial result to the results.

        Parameters
        ----------
        index : int
            index of the molecule
        x : np.ndarray
            array of the correlation results

        """
        for ax_ind, axis in enumerate("xyz"):
            self._outputData[f"{axis}_rotation_ac"] += x[0][ax_ind]
            self._outputData[f"rotation_around_{axis}"] += x[1][:, ax_ind]

    def finalize(self):
        """Normalise and write out the results."""

        for axis in "xyz":
            self._outputData[f"{axis}_rotation_ac"] /= self.numberOfSteps
            self._outputData[f"rotation_around_{axis}"] /= self.numberOfSteps

        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
