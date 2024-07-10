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
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class UnfoldedTrajectory(IJob):
    """
    Tries to make a contiguous trajectory for a whole molecule e.g. a protein.

    The routine may fail if the molecule is bigger than half of the box side (L/2) and or the initial structure is not in itself contiguous.
    """

    label = "Unfolded Trajectory"

    category = (
        "Analysis",
        "Trajectory",
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
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

        # The collection of atoms corresponding to the atoms selected for output.
        indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        self._selectedAtoms = [atoms[ind] for ind in indexes]

        # The output trajectory is opened for writing.
        self._outputTraj = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self.configuration["trajectory"]["instance"].chemical_system,
            self.numberOfSteps,
            self._selectedAtoms,
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)

        conf = conf.continuous_configuration()

        cloned_conf = conf.clone(self._outputTraj.chemical_system)

        self._outputTraj.chemical_system.configuration = cloned_conf

        # The time corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        # Write the step.
        self._outputTraj.dump_configuration(time)

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        # The input trajectory is closed.
        self.configuration["trajectory"]["instance"].close()

        # The output trajectory is closed.
        self._outputTraj.close()
        super().finalize()
