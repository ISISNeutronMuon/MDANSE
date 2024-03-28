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
from MDANSE.MolecularDynamics.Analysis import mean_square_fluctuation
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class RootMeanSquareFluctuation(IJob):
    """
    The root mean square fluctuation (RMSF) for a set of atoms is similar to the square root
        of the mean square displacement (MSD), except that it is spatially resolved (by atom/residue/etc)
        rather than time resolved. It reveals the dynamical heterogeneity of the molecule over the course
        of a MD simulation.
    """

    label = "Root Mean Square Fluctuation"

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
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
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
        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        # Will store the indexes.
        indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        self._outputData.add("indexes", "LineOutputVariable", indexes)

        # Will store the mean square fluctuation evolution.
        self._outputData.add(
            "rmsf",
            "LineOutputVariable",
            (self.configuration["atom_selection"]["selection_length"],),
            axis="indexes",
            units="nm",
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
            #. rmsf (np.array): the calculated root mean square fluctuation for atom index
        """
        # read the particle trajectory
        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        rmsf = mean_square_fluctuation(series, root=True)

        return index, rmsf

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["rmsf"][index] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
