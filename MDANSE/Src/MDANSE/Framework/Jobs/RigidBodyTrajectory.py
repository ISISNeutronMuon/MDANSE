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

import h5py

from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.LinearAlgebra import Quaternion, Vector
from MDANSE.Mathematics.Transformation import Translation
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import (
    RigidBodyTrajectoryGenerator,
    TrajectoryWriter,
)


class RigidBodyTrajectory(IJob):
    """In MDANSE, Rigid-Body Trajectory (RBT) can be defined from a MD trajectory
    by fitting rigid reference structures, defining a (sub)molecule,
    to the corresponding structure in each time frame of the trajectory.
    Here 'fit' means the optimal superposition of the structures in a least-squares sense.
    Global translations and rotations of molecules or subunits of complex molecules
    can be extracted from a MD trajectory.

    A more detailed presentation is given in
    G. R. Kneller, 'Superposition of Molecular Structures using Quaternions,'
    Mol. Simul., vol. 7, no. 1-2, pp. 113-119, May 1991,
    doi: 10.1080/08927029108022453.
    """

    enabled = False

    label = "Rigid Body Trajectory"

    category = (
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
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "default": "atom",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            },
        },
    )
    settings["reference"] = ("IntegerConfigurator", {"mini": 0})
    settings["remove_translation"] = ("BooleanConfigurator", {"default": False})
    settings["output_files"] = ("OutputTrajectoryConfigurator", {"format": "MDTFormat"})

    def initialize(self):
        """ """
        super().initialize()

        if (
            self.configuration["reference"]["value"]
            >= self.configuration["trajectory"]["length"]
        ):
            raise JobError(
                self,
                "Invalid reference frame. Must be an integer in "
                f"[{0},{self.configuration['trajectory']['length']}[",
            )

        self._quaternions = np.zeros(
            (
                self.configuration["atom_selection"]["selection_length"],
                self.configuration["frames"]["number"],
                4,
            ),
            dtype=np.float64,
        )
        self._coms = np.zeros(
            (
                self.configuration["atom_selection"]["selection_length"],
                self.configuration["frames"]["number"],
                3,
            ),
            dtype=np.float64,
        )
        self._fits = np.zeros(
            (
                self.configuration["atom_selection"]["selection_length"],
                self.configuration["frames"]["number"],
            ),
            dtype=np.float64,
        )

        atoms = self.trajectory.chemical_system.atom_list

        self._groups = []

        for i in range(self.configuration["atom_selection"]["selection_length"]):
            indices = self.configuration["atom_selection"]["indices"][i]
            self._groups.append(
                AtomCluster("", [atoms[idx] for idx in indices], parentless=True)
            )

        self.numberOfSteps = len(self._groups)

        self.referenceFrame = self.configuration["reference"]["value"]

        trajectory = self.trajectory

        coords = trajectory.coordinates(self.referenceFrame)
        unitCell = trajectory.unit_cell(self.referenceFrame)

        selectedAtoms = []
        for indices in self.configuration["atom_selection"]["indices"]:
            for idx in indices:
                selectedAtoms.append(atoms[idx])

        # Create trajectory
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            trajectory.chemical_system,
            self.configuration["frames"]["number"],
            selectedAtoms,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
        )

        self._group_atoms = [group.atom_list for group in self._groups]

        conf = RealConfiguration(
            self._output_trajectory.chemical_system, coords, unitCell
        )

        self._reference_configuration = conf.continuous_configuration()

    def run_step(self, index):
        """ """

        trajectory = self.trajectory

        rbt = RigidBodyTrajectoryGenerator(
            trajectory,
            self._groups[index],
            self._reference_configuration,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        self._quaternions[index, :, :] = rbt.quaternions
        self._coms[index, :, :] = rbt.cms
        self._fits[index, :] = rbt.fit

        return index, None

    def combine(self, index, x):
        """ """

        pass

    def finalize(self):
        """ """

        group_coms = [
            center_of_mass(self._reference_configuration[group])
            for group in self._groups
        ]

        trajectory = self.trajectory

        for i in range(self._quaternions.shape[1]):
            current_frame = self.configuration["frames"]["value"][i]
            time = self.configuration["frames"]["time"][i]

            real_configuration = trajectory.configuration(current_frame).clone(
                self._output_trajectory.chemical_system
            )

            for group_id in range(self._quaternions.shape[0]):
                center_of_mass = group_coms[group_id]

                # The rotation matrix corresponding to the selected frame in the RBT.
                transfo = Quaternion(self._quaternions[group_id, i, :]).asRotation()

                if self.configuration["remove_translation"]["value"]:
                    # The transformation matrix corresponding to the selected frame in the RBT.
                    transfo = Translation(Vector(*center_of_mass)) * transfo

                # Compose with the CMS translation if the removeTranslation flag is set off.
                else:
                    # The transformation matrix corresponding to the selected frame in the RBT.
                    transfo = Translation(Vector(self._coms[group_id, i, :])) * transfo

                # Loop over the atoms of the group to set the RBT trajectory.
                for atom in self._group_atoms[group_id]:
                    # The coordinates of the atoms are centered around the center of mass of the group.
                    xyz = (
                        self._reference_configuration["coordinates"][atom.index, :]
                        - center_of_mass
                    )

                    real_configuration["coordinates"][atom.index, :] = transfo(
                        Vector(*xyz)
                    )

            self._output_trajectory.dump_configuration(
                real_configuration,
                time,
                units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
            )

        outputFile = h5py.File(self.configuration["output_files"]["file"], "r+")

        n_groups = self.configuration["atom_selection"]["selection_length"]
        n_frames = self.configuration["frames"]["number"]

        quaternions = outputFile.create_dataset(
            "quaternions", shape=(n_groups, n_frames, 4), dtype=np.float64
        )

        coms = outputFile.create_dataset(
            "coms", shape=(n_groups, n_frames, 3), dtype=np.float64
        )

        fits = outputFile.create_dataset(
            "fits", shape=(n_groups, n_frames), dtype=np.float64
        )

        outputFile.attrs["info"] = str(self)

        # Loop over the groups.
        for comp in range(self.configuration["atom_selection"]["selection_length"]):
            aIndexes = self.configuration["atom_selection"]["indices"][comp]

            outputFile.attrs["info"] += f"Group {comp}: {list(aIndexes)}\n"

            quaternions[comp, :, :] = self._quaternions[comp, :, :]
            coms[comp, :, :] = self._coms[comp, :, :]
            fits[comp, :] = self._fits[comp, :]

        outputFile.close()
        super().finalize()
