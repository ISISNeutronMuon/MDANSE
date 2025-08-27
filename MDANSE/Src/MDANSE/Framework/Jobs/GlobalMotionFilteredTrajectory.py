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
import copy

import h5py
import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class GlobalMotionFilteredTrajectory(IJob):
    """
    It is often of interest to separate global translation and rotation motion from internal motion, both for quantitative analysis
    and for visualization by animated display. Obviously, this can only be done under the hypothesis that global and internal motions
    are decoupled within the length and timescales of the analysis. MDANSE creates a Global Motion Filtered Trajectory (GMFT) by
    filtering out global motions (made of the three translational and three rotational degrees of freedom), either on the whole system
    or on an user-defined subset, by fitting it to a reference structure (usually the first frame of the MD). Global motion filtering
    uses a straightforward algorithm:

    #. for the first frame, find the linear transformation such that the coordinate origin becomes the centre of mass of the system
    and its principal axes of inertia are parallel to the three coordinates axes (also called principal axes transformation),
    #. this provides a reference configuration *r*
    #. for any other frames *f*, find and apply the linear transformation that minimizes the RMS 'distance' between frame *f* and *r*.

    The result is stored in a new trajectory file that contains only internal motions. This analysis can be useful in case where
    overall diffusive motions are not of interest e.g. for a protein in solution and the internal protein dynamics fall within the
    dynamical range of the instrument.

    In the global motion filtered trajectory, the universe is made infinite and all the configurations contiguous.
    """

    enabled = False

    label = "Global Motion Filtered Trajectory"

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
    settings["reference_selection"] = (
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

        # The collection of atoms corresponding to the atoms selected for output.
        atoms = self.trajectory.atom_types
        self._selected_atoms = self.trajectory.atom_indices

        self._reference_atoms = []
        for indices in self.configuration["reference_selection"]["indices"]:
            for idx in indices:
                self._reference_atoms.append(atoms[idx])

        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self.trajectory.chemical_system,
            self.numberOfSteps,
            self._selected_atoms.atom_list,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
        )

        # This will store the configuration used as the reference for the following step.
        self._reference_configuration = None

        self._rms = []

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

        trajectory = self.trajectory

        current_configuration = trajectory.configuration(frameIndex)
        current_configuration = current_configuration.continuous_configuration()
        variables = copy.deepcopy(current_configuration.variables)
        coords = variables.pop("coordinates")
        current_configuration = RealConfiguration(
            trajectory.chemical_system, coords, **variables
        )

        # Case of the first frame.
        if frameIndex == self.configuration["frames"]["first"]:
            # A a linear transformation that shifts the center of mass of the reference atoms to the coordinate origin
            # and makes its principal axes of inertia parallel to the three coordinate axes is computed.
            transfo = self._reference_atoms.normalizing_transformation(
                current_configuration
            )

            # The first rms is set to zero by construction.
            rms = 0.0

        # Case of the other frames.
        else:
            # The linear transformation that minimizes the RMS distance between the current configuration and the previous
            # one is applied to the reference atoms.
            transfo, rms = self._reference_atoms.find_transformation(
                current_configuration, self._reference_configuration
            )

        # And applied to the selected atoms for output.
        current_configuration.apply_transformation(transfo)

        # The current configuration becomes now the reference configuration for the next step.
        self._reference_configuration = current_configuration

        variables = copy.deepcopy(current_configuration.variables)
        coords = variables.pop("coordinates")
        new_configuration = RealConfiguration(
            self._output_trajectory.chemical_system, coords, None, **variables
        )
        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        # Write the step.
        self._output_trajectory.dump_configuration(
            new_configuration,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )

        return index, rms

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._rms.append(x)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        # The input trajectory is closed.
        self.trajectory.close()

        # The output trajectory is closed.
        self._output_trajectory.close()

        outputFile = h5py.File(self.configuration["output_files"]["file"], "r+")

        outputFile.create_dataset("rms", data=self._rms, dtype=np.float64)

        outputFile.close()
        super().finalize()
