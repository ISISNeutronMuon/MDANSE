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

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
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

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 1, 1)},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates in to box"},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            },
            "default": "molecule",
        },
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
        chemical_system = self.trajectory.chemical_system

        self.cluster_composition = {}
        original_atom_list = chemical_system.atom_list
        selected_indices = (
            set(self.trajectory._selection)
            if self.trajectory._selection
            else set(chemical_system._atom_indices)
        )
        new_element_list = []
        used_up_atoms = set()
        new_chemical_system = ChemicalSystem()
        for cluster_name in chemical_system._clusters.keys():
            for cluster in chemical_system._clusters[cluster_name]:
                if selected_indices and set(cluster) <= selected_indices:
                    if cluster_name not in self.cluster_composition:
                        self.cluster_composition[cluster_name] = [
                            original_atom_list[ind] for ind in cluster
                        ]
                    new_element_list.append(cluster_name)
                    used_up_atoms.update(set(cluster))
        for index in selected_indices:
            if index not in used_up_atoms:
                new_element_list.append(chemical_system.atom_list[index])
        self._used_up_atoms = used_up_atoms
        new_chemical_system.initialise_atoms(new_element_list)

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            new_chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
        )
        self._unique_atoms = np.unique(new_element_list)
        self._molecule_radii = {
            cluster_name: [] for cluster_name in chemical_system._clusters.keys()
        }
        self.selected_indices = selected_indices

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
        chemical_system = self.trajectory.chemical_system
        atom_database = self.trajectory

        n_coms = self._output_trajectory.chemical_system.number_of_atoms

        conf = self.trajectory.configuration(frameIndex)
        conf = conf.contiguous_configuration()
        temp_radii = {
            cluster_name: [] for cluster_name in chemical_system._clusters.keys()
        }

        com_coords = np.empty((n_coms, 3), dtype=np.float64)
        mol_index = 0
        for cluster_name in chemical_system._clusters.keys():
            for cluster in chemical_system._clusters[cluster_name]:
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
        for atom_index in self.selected_indices:
            if atom_index not in self._used_up_atoms:
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

        if self.configuration["fold"]["value"]:
            com_conf.fold_coordinates()

        for cluster_name, radii in temp_radii.items():
            self._molecule_radii[cluster_name].append(np.mean(radii))
        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(com_conf, time)

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

        time_averaged_radii = {
            cluster_name: np.mean(self._molecule_radii[cluster_name])
            for cluster_name in self._molecule_radii.keys()
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
