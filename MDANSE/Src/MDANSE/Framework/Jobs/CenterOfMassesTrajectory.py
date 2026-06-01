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

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    Boolean,
    FrameSelect,
    GroupingLevel,
    MDANSETrajectory,
    OutputTrajectory,
)
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class CenterOfMassesTrajectory(IJob):
    """Outputs a trajectory where molecules have been replaced by artificial particles.

    Creates a trajectory from the centre of masses for selected groups of atoms in a
    given input trajectory. The resulting trajectory will not include the internal
    vibrations of molecules or the rotational modes.
    """

    label = "Center Of Masses Trajectory"

    category = ("Trajectory",)
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(selection="atom_selection")
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(
        depends={"trajectory": "trajectory"},
        default={"0": {"function_name": "select_all", "operation_type": "union"}},
    )
    fold = Boolean(label="Fold coordinates in to box")
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = len(self.frames)
        chemical_system = self.trajectory.chemical_system

        self.cluster_composition: dict[str, list[str]] = {}
        original_atom_list = chemical_system.atom_list
        selected_indices: set[int] = (
            set(self.trajectory._selection)
            if self.trajectory._selection
            else set(chemical_system._atom_indices)
        )
        new_element_list = []
        used_up_atoms = set()
        new_chemical_system = ChemicalSystem()

        for cluster_name, clusters in chemical_system._clusters.items():
            for cluster in clusters:
                if selected_indices and set(cluster) <= selected_indices:
                    if cluster_name not in self.cluster_composition:
                        self.cluster_composition[cluster_name] = [
                            original_atom_list[ind] for ind in cluster
                        ]
                    new_element_list.append(cluster_name)
                    used_up_atoms.update(set(cluster))

        new_element_list.extend(
            chemical_system.atom_list[index]
            for index in selected_indices - used_up_atoms
        )

        self._used_up_atoms = used_up_atoms
        new_chemical_system.initialise_atoms(new_element_list)

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.output_files.path,
            new_chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
        )
        self._unique_atoms = np.unique(new_element_list)
        self._molecule_radii = {
            cluster_name: [] for cluster_name in chemical_system._clusters
        }
        self.selected_indices = selected_indices

    def run_step(self, index: int) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            Index of the loop.

        Returns
        -------
        tuple[int, None]
        """

        # get the Frame index
        frameIndex = self.frames[index].ind
        chemical_system = self.trajectory.chemical_system
        atom_database = self.trajectory

        n_coms = self._output_trajectory.chemical_system.number_of_atoms

        conf = self.trajectory.configuration(frameIndex)

        conf = conf.contiguous_configuration()
        temp_radii: dict[str, list[float]] = {
            cluster_name: [] for cluster_name in chemical_system._clusters
        }

        com_coords = np.empty((n_coms, 3), dtype=np.float64)
        mol_index = 0

        for cluster_name, clusters in chemical_system._clusters.items():
            for cluster in clusters:
                if not set(cluster).issubset(self.selected_indices):
                    continue
                masses = [
                    atom_database.get_atom_property(
                        chemical_system.atom_list[cluster_index], "atomic_weight"
                    )
                    for cluster_index in cluster
                ]
                individual_coordinates = conf.coordinates[cluster]
                centre_of_mass = center_of_mass(individual_coordinates, masses)
                com_coords[mol_index] = centre_of_mass
                average_radius = individual_coordinates - centre_of_mass.reshape(1, 3)
                average_radius = np.linalg.norm(average_radius, axis=1)
                average_radius = np.average(average_radius, weights=masses)
                temp_radii[cluster_name].append(average_radius)
                mol_index += 1

        for atom_index in set(self.selected_indices) - self._used_up_atoms:
            com_coords[mol_index] = conf.coordinates[atom_index]
            mol_index += 1

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system, com_coords, conf.unit_cell
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system, com_coords
            )

        if self.fold:
            com_conf.fold_coordinates()

        for cluster_name, radii in temp_radii.items():
            self._molecule_radii[cluster_name].append(np.mean(radii))

        # The times corresponding to the running index.
        time = self.frames.times[index]

        self._output_trajectory.dump_configuration(com_conf, time)

        return index, None

    def combine(self, _index, _x):
        """Dummy combine step.

        Parameters
        ----------
        _index : int
            Unused.
        _x : None
            Unused.
        """

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        time_averaged_radii = {
            cluster_name: np.mean(radii)
            for cluster_name, radii in self._molecule_radii.items()
        }

        self._output_trajectory.write_atom_database(
            self._unique_atoms,
            self.trajectory,
            self.cluster_composition,
            time_averaged_radii,
        )
        # The input trajectory is closed.
        self.trajectory.close()
        write_metadata(self, self._output_trajectory._h5_file)

        # The output trajectory is closed.
        self._output_trajectory.close()
        super().finalize()
