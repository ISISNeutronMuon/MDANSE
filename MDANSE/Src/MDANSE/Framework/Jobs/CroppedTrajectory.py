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


from MDANSE.Chemistry.ChemicalEntity import AtomGroup
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class CroppedTrajectory(IJob):
    """
    Crop a trajectory in terms of the contents of the simulation box (selected atoms or molecules) and the trajectory length.
    """

    enabled = False

    label = "Cropped Trajectory"

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
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

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
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self.configuration["trajectory"]["instance"].chemical_system,
            self.numberOfSteps,
            self._selectedAtoms,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
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
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)

        cloned_conf = conf.clone(self._output_trajectory.chemical_system)

        self._output_trajectory.chemical_system.configuration = cloned_conf

        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(time)

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
        self._output_trajectory.close()
