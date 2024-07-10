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
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import normalize
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class PositionAutoCorrelationFunction(IJob):
    """
    Like the velocity autocorrelation function, but using positions instead of velocities.
    """

    label = "Position AutoCorrelation Function"

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
    settings["normalize"] = ("BooleanConfigurator", {"default": False})
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            }
        },
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(log_filename, self.configuration["output_files"]["log_level"])

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will store the mean square displacement evolution.
        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "pacf_%s" % element,
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="nm2",
                main_result=True,
                partial_result=True,
            )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicPACF (np.array): The calculated position auto-correlation function for atom index
        """

        # get atom index
        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = series - np.average(series, axis=0)
        series = self.configuration["projection"]["projector"](series)

        n_configs = self.configuration["frames"]["n_configs"]
        atomicPACF = correlate(series, series[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, atomicPACF.T[0]

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration["atom_selection"]["names"][index]

        # The MSD for element |symbol| is updated.
        self._outputData["pacf_%s" % element] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        self.configuration["atom_selection"]["n_atoms_per_element"] = nAtomsPerElement

        for element, number in list(nAtomsPerElement.items()):
            self._outputData["pacf_%s" % element] /= number

        if self.configuration["normalize"]["value"]:
            for element in list(nAtomsPerElement.keys()):
                if self._outputData["pacf_%s" % element][0] == 0:
                    raise ValueError("The normalization factor is equal to zero !!!")
                else:
                    self._outputData["pacf_%s" % element] = normalize(
                        self._outputData["pacf_%s" % element], axis=0
                    )

        weights = self.configuration["weights"].get_weights()
        pacfTotal = weight(weights, self._outputData, nAtomsPerElement, 1, "pacf_%s")

        self._outputData.add(
            "pacf_total",
            "LineOutputVariable",
            pacfTotal,
            axis="time",
            units="nm2",
            main_result=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
