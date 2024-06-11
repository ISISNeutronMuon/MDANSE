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


from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight


class DensityProfileError(Error):
    pass


class DensityProfile(IJob):
    """
    The Density Profile analysis shows the weighted atomic density heterogeneity in the directions of the simulation box axes.
    For a lipid membrane, the density variation in the direction perpendicular to the membrane is probed in reflectometry measurements.
    The Density Profile Analysis can show segregation or cluster order formation, for example during the formation of micelles.
    """

    label = "Density Profile"

    category = (
        "Analysis",
        "Structure",
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
    settings["axis"] = (
        "SingleChoiceConfigurator",
        {"choices": ["a", "b", "c"], "default": "c"},
    )
    settings["dr"] = ("FloatConfigurator", {"default": 0.01, "mini": 1.0e-9})
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

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["frames"]["number"]

        self._dr = self.configuration["dr"]["value"]

        axis_index = self.configuration["axis"]["index"]

        first_conf = self.configuration["trajectory"][
            "instance"
        ].chemical_system.configuration

        try:
            axis = first_conf.unit_cell.direct[axis_index, :]
        except:
            raise DensityProfileError(
                "Density profile cannot be computed without a simulation box"
            )

        axis_length = np.sqrt(np.sum(axis**2))
        self._n_bins = int(axis_length / self._dr) + 1

        self._outputData.add("r", "LineOutputVariable", (self._n_bins,), units="nm")

        self._indexes_per_element = self.configuration["atom_selection"].get_indexes()

        for element in self._indexes_per_element.keys():
            self._outputData.add(
                "dp_%s" % element,
                "LineOutputVariable",
                (self._n_bins,),
                axis="r",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._extent = 0.0

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)

        box_coords = conf.to_box_coordinates()

        axis_index = self.configuration["axis"]["index"]
        axis = conf.unit_cell.direct[axis_index, :]
        axis_length = np.sqrt(np.sum(axis**2))

        dp_per_frame = {}

        for k, v in self._indexes_per_element.items():
            h = np.histogram(
                box_coords[v, axis_index], bins=self._n_bins, range=[-0.5, 0.5]
            )
            dp_per_frame[k] = h[0]

        return index, (axis_length, dp_per_frame)

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        self._extent += x[0]

        for element, hist in list(x[1].items()):
            self._outputData["dp_%s" % element] += hist

    def finalize(self):
        """
        Finalize the job.
        """

        n_atoms_per_element = self.configuration["atom_selection"].get_natoms()
        for element in n_atoms_per_element.keys():
            self._outputData["dp_%s" % element] += self.numberOfSteps

        dp_total = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            n_atoms_per_element,
            1,
            "dp_%s",
        )

        self._outputData.add(
            "dp_total", "LineOutputVariable", dp_total, axis="r", units="au"
        )

        self._extent /= self.numberOfSteps

        r_values = self._extent * np.linspace(0, 1, self._n_bins + 1)
        self._outputData["r"][:] = (r_values[1:] + r_values[:-1]) / 2

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
