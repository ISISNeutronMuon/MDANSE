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
import collections

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import differentiate, get_spectrum


class Infrared(IJob):

    enabled = True

    label = "Dipole AutoCorrelation Function"

    category = (
        "Analysis",
        "Infrared",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["molecule_name"] = (
        "MoleculeSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["atom_charges"] = (
        "PartialChargeConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": {},
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(log_filename, self.configuration["output_files"]["log_level"])

        ce_list = self.configuration["trajectory"][
            "instance"
        ].chemical_system.chemical_entities
        self.molecules = [
            ce
            for ce in ce_list
            if ce.name == self.configuration["molecule_name"]["value"]
        ]

        self.numberOfSteps = len(self.molecules)
        instrResolution = self.configuration["instrument_resolution"]

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="time",
            units="au",
        )

        self._outputData.add(
            "omega", "LineOutputVariable", instrResolution["romega"], units="rad/ps"
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        self._outputData.add(
            "ddacf",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
        )
        self._outputData.add(
            "ir",
            "LineOutputVariable",
            (instrResolution["n_romegas"],),
            axis="omega",
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
            The index of the step and the calculated d/dt dipole
            auto-correlation function for a molecule.
        """
        molecule = self.molecules[index]
        ddipole = np.zeros(
            (self.configuration["frames"]["number"], 3), dtype=np.float64
        )
        for i, frame_index in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            )
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index
            )
            contiguous_configuration = configuration.contiguous_configuration()
            com = molecule.center_of_mass(contiguous_configuration)

            for atm in molecule.atom_list:
                idx = atm.index
                q = self.configuration["atom_charges"]["charges"][idx]
                ddipole[i] = q * (contiguous_configuration["coordinates"][idx, :] - com)

        for axis in range(3):
            ddipole[:, axis] = differentiate(
                ddipole[:, axis],
                order=2,
                dt=self.configuration["frames"]["time_step"],
            )

        n_configs = self.configuration["frames"]["n_configs"]
        mol_ddacf = correlate(ddipole, ddipole[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, mol_ddacf.T[0]

    def combine(self, index, x):
        """Combines returned results of run_step."""
        self._outputData["ddacf"] += x

    def finalize(self):
        """Finalizes the calculations (e.g. averaging the total term,
        output files creations ...).
        """
        self._outputData["ddacf"] /= self.numberOfSteps
        self._outputData["ir"][:] = get_spectrum(
            self._outputData["ddacf"],
            self.configuration["instrument_resolution"]["time_window"],
            self.configuration["instrument_resolution"]["time_step"],
            fft="rfft",
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
