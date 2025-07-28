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

import collections

import numpy as np
from scipy.signal import correlate
from scipy.spatial.transform import Rotation

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia


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

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["molecule"] = (
        "MoleculeSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        molecules = self.trajectory.chemical_system._clusters[
            self.configuration["molecule"]["value"]
        ]

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
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "frame",
            "LineOutputVariable",
            np.arange(self.configuration["frames"]["number"]),
            units="ps",
        )

        self._outputData.add(
            "axis_index",
            "LineOutputVariable",
            np.arange(
                self.configuration["trajectory"][
                    "instance"
                ].chemical_system.number_of_molecules(
                    self.configuration["molecule"]["value"],
                ),
            ),
            units="au",
        )

        for axis in "xyz":
            self._outputData.add(
                f"rotation_around_{axis}",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="frame",
                units="au",
            )
            self._outputData.add(
                f"{axis}_rotation_ac",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
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

        euler_angles = np.empty((self.configuration["frames"]["number"], 3))
        ref_coords = None

        for i, frame_index in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            ),
        ):
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

        n_configs = self.configuration["frames"]["n_configs"]
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
        for ax_ind, axis in enumerate(["x", "y", "z"]):
            self._outputData[f"{axis}_rotation_ac"] += x[0][ax_ind]
            self._outputData[f"rotation_around_{axis}"] += x[1][:, ax_ind]

    def finalize(self):
        """Normalise and write out the results."""

        for ax_ind, axis in enumerate(["x", "y", "z"]):
            self._outputData[f"{axis}_rotation_ac"] /= self.numberOfSteps
            self._outputData[f"rotation_around_{axis}"] /= self.numberOfSteps

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
