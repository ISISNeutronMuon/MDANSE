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

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob


class RootMeanSquareDeviation(IJob):
    """Calculates the Root Mean Square Deviation of the selected atoms.

    The Root Mean-Square Deviation (RMSD) is one of the most popular measures
    of structural similarity. It is a numerical measure of the difference
    between two structures. Typically, the RMSD is used to quantify the structural
    evolution of the system during the simulation. It can provide essential
    information about the structure, if it reached equilibrium or conversely
    if major structural changes occurred during the simulation.
    """

    label = "Root Mean Square Deviation"

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
    settings["reference_frame"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
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
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)

        self._referenceIndex = self.configuration["reference_frame"]["value"]

        # Will store the time.
        self._outputData.add(
            "rmsd/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will initially store the mean square deviation before appling the root
        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"rmsd/{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="rmsd/axes/time",
                units="nm",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "rmsd/total",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="rmsd/axes/time",
            units="nm",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        atom_index = self.trajectory.atom_indices[index]

        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        # Compute the squared sum of the difference between all the coordinate of atoms i and the reference ones
        squaredDiff = np.sum((series - series[self._referenceIndex, :]) ** 2, axis=1)

        return index, squaredDiff

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        element = self._atoms[self.trajectory.atom_indices[index]]

        self._outputData[f"rmsd/{element}"] += x
        self._outputData["rmsd/total"] += x

    def finalize(self):
        """
        Finalize the job.
        """
        n_atms = self.trajectory.get_total_natoms()

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "rmsd",
            "LineOutputVariable",
            axis="rmsd/axes/time",
            units="nm",
            scaling_factor=False,
            post_func=lambda x: np.sqrt(x / n_atms),
            post_label="total",
            main_result=True,
            partial_result=True,
        )

        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"rmsd/{element}"][:] = np.sqrt(
                self._outputData[f"rmsd/{element}"] / number
            )

        self._outputData["rmsd/total"][:] = np.sqrt(
            self._outputData["rmsd/total"] / n_atms
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
