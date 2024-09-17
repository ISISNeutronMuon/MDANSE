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


class DipoleAutoCorrelationFunction(IJob):

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
        super().initialize()

        ce_list = self.configuration["trajectory"][
            "instance"
        ].chemical_system.chemical_entities
        self.molecules = [
            ce
            for ce in ce_list
            if ce.name == self.configuration["molecule_name"]["value"]
        ]

        self.numberOfSteps = len(self.molecules)

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "dacf",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
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
        dipoles = np.zeros(
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
            charges = self.configuration["trajectory"]["instance"].charges(frame_index)
            contiguous_configuration = configuration.contiguous_configuration()
            com = molecule.center_of_mass(contiguous_configuration)

            for atm in molecule.atom_list:
                idx = atm.index
                try:
                    q = self.configuration["atom_charges"]["charges"][idx]
                except KeyError:
                    q = charges[idx]
                dipoles[i] = q * (contiguous_configuration["coordinates"][idx, :] - com)

        n_configs = self.configuration["frames"]["n_configs"]
        mol_dacf = correlate(dipoles, dipoles[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, mol_dacf.T[0]

    def combine(self, index, x):
        """Combines returned results of run_step."""
        self._outputData["dacf"] += x

    def finalize(self):
        """Finalizes the calculations (e.g. averaging the total term,
        output files creations ...).
        """
        self._outputData["dacf"] /= self.numberOfSteps

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
