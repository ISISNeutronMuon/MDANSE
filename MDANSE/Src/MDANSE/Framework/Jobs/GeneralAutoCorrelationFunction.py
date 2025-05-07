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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import correlation, normalisation_factor


class GeneralAutoCorrelationFunction(IJob):
    """
    Computes the autocorrelation for any available trajectory variable.
    """

    enabled = False

    label = "General AutoCorrelation Function"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
    settings["trajectory_variable"] = (
        "TrajectoryVariableConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
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
        super().initialize()

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
                f"gacf_{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="time",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "gacf_total",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
            units="au",
            main_result=True,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): the index of the step.
        :Returns:
            #. index (int): the index of the step.
            #. atomicGACF (np.array): the calculated auto-correlation function for the index
        """

        indices = self.configuration["atom_selection"]["indices"][index]

        series = self.configuration["trajectory"][
            "instance"
        ].read_configuration_trajectory(
            indices[0],
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
            variable=self.configuration["trajectory_variable"]["value"],
        )

        atomicGACF = correlation(series, axis=0, average=1)

        return index, atomicGACF

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        element = self.configuration["atom_selection"]["names"][index]

        self._outputData[f"gacf_{element}"] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        self.configuration["atom_selection"]["n_atoms_per_element"] = nAtomsPerElement

        for element, number in nAtomsPerElement.items():
            self._outputData[f"gacf_{element}"] /= number

        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)
        assign_weights(self._outputData, weight_dict, "gacf_%s")
        gacfTotal = weighted_sum(self._outputData, weight_dict, "gacf_%s")

        self._outputData["gacf_total"][:] = gacfTotal

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
