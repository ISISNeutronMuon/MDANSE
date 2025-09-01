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

from more_itertools import always_iterable

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class CroppedTrajectory(IJob):
    """Outputs a subset of frames or atoms of the input trajectory.

    Crop a trajectory in terms of the contents of the simulation box
    (selected atoms or molecules) and the trajectory length.
    """

    enabled = False

    label = "Cropped Trajectory"

    category = ("Trajectory",)

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

        atoms = self.trajectory.atom_types
        indices = self.trajectory.atom_indices

        self._selectedAtoms = always_iterable(self.trajectory.selection_getter(atoms))
        self._selected_indices = indices

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self.trajectory.chemical_system,
            self.numberOfSteps,
            self._selected_indices,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=[self.trajectory.charges(0)[ind] for ind in indices],
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

        conf = self.trajectory.configuration(frame_index)

        cloned_conf = conf.clone(self._output_trajectory.chemical_system)

        time = self.configuration["frames"]["time"][index]

        charge = self.trajectory.charges(index)[self._selected_indices]

        self._output_trajectory.dump_configuration(cloned_conf, time)

        self._output_trajectory.write_charges(charge, index)

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
        self.trajectory.close()

        # The output trajectory is closed.
        self._output_trajectory.close()
        super().finalize()
