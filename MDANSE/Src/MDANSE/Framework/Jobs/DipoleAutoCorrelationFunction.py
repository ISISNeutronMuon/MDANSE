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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    CorrelationWindow,
    DynamicSingleChoice,
    FrameSelect,
    MDANSETrajectory,
    OutputFile,
    PartialCharge,
    RunningMode,
)
from MDANSE.Mathematics.Geometry import center_of_mass


class DipoleAutoCorrelationFunction(IJob):
    """Calculates the Dipole Autocorrelation Function of a system.

    Partial charges need to be defined in the system for this analysis
    to produce non-zero results.
    """

    enabled = True

    label = "Dipole AutoCorrelation Function"

    category = (
        "Analysis",
        "Infrared",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory()
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    molecule_name = DynamicSingleChoice[str, str](
        choices="chemical_system._clusters.keys()",
        depends={"choices": "trajectory"},
        label="Molecule name",
    )
    atom_charges = PartialCharge(depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.chemical_system = self.trajectory.chemical_system

        self.molecules = self.chemical_system._clusters[self.molecule_name]

        self.numberOfSteps = len(self.molecules)

        # Will store the time.
        self._outputData.add(
            "dacf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )

        self._outputData.add(
            "dacf/dacf",
            "LineOutputVariable",
            (self.frame_window.n_frames,),
            axis="dacf/axes/time",
            main_result=True,
        )

    def run_step(self, index) -> tuple[int, np.ndarray]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            The index of the step.

        Returns
        -------
        tuple[int, np.ndarray]
            The index of the step and the calculated dipole
            auto-correlation function for a molecule.
        """
        molecule = self.molecules[index]
        dipoles = np.zeros((len(self.frames), 3), dtype=np.float64)
        for i, frame_index in enumerate(
            range(
                self.frames.index_start,
                self.frames.index_stop + 1,
                self.frames.index_step,
            )
        ):
            configuration = self.trajectory.configuration(frame_index)
            masses = [
                self.trajectory.get_atom_property(
                    self.chemical_system.atom_list[index], "atomic_weight"
                )
                for index in molecule
            ]
            charges = self.trajectory.charges(frame_index)
            contiguous_configuration = configuration.contiguous_configuration()
            coords = contiguous_configuration.coordinates[molecule]
            com = center_of_mass(coords, masses)

            for idx in molecule:
                try:
                    q = self.atom_charges[idx]
                except KeyError:
                    q = charges[idx]
                dipoles[i] += q * (
                    contiguous_configuration["coordinates"][idx, :] - com
                )

        n_configs = self.frame_window.n_configs
        mol_dacf = correlate(dipoles, dipoles[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, mol_dacf.T[0]

    def combine(self, index, x):
        """Combines returned results of run_step."""
        self._outputData["dacf/dacf"] += x

    def finalize(self):
        """Finalizes the calculations (e.g. averaging the total term,
        output files creations ...).
        """
        self._outputData["dacf/dacf"] /= self.numberOfSteps

        self._outputData.write(
            self.output_files.root,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
