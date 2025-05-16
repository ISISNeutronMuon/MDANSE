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

from MDANSE.Chemistry.GroupingTool import GroupingTool
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import normalisation_factor


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
        {},
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
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]
        self._grouper = GroupingTool(
            self.configuration["trajectory"]["instance"].chemical_system,
            self._outputData,
        )
        self._grouper.set_selection(
            self.configuration["atom_selection"]["flatten_indices"]
        )
        self._grouper.set_dataset_parameters(
            {
                "output_type": "LineOutputVariable",
                "dimensions": (self.configuration["frames"]["n_frames"],),
                "axis": "time",
                "units": "nm2",
                "main_result": True,
                "partial_result": True,
            }
        )
        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_list

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()

        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)
        self._grouper.set_weight_dictionary(weight_dict)

        self._grouper.set_grouping(self.configuration["grouping_level"]["value"])
        self._grouper.create_result_groups("pacf")
        self._grouper.set_atom_masses(self.configuration["trajectory"]["instance"])

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
        indices = self.configuration["atom_selection"]["indices"][index]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            indices,
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
        self._grouper.assign_result(
            self.configuration["atom_selection"]["flatten_indices"][index], x
        )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        self._grouper.finalise_centre_of_mass()
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
