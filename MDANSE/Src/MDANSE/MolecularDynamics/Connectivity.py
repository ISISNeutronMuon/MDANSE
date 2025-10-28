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

from collections.abc import Iterable
from itertools import product

import numpy as np
from scipy.spatial import KDTree

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class Connectivity:
    """This class calculates the distances between atoms in a trajectory,
    and identifies potential molecules based on distances alone.
    """

    def __init__(
        self,
        trajectory: Trajectory,
        selection: list[int] | None = None,
    ):
        self._input_trajectory = trajectory
        self._selection = selection or trajectory._selection or trajectory.atom_indices
        self._periodic = self._input_trajectory.configuration(0).is_periodic
        self.check_composition()
        self._bonds = None
        self._bond_mapping = None
        self._unique_bonds = None
        self._translation_vectors = {}

    def check_composition(self):
        """Get atom types and radii from the trajectory."""
        atom_elements = list(
            np.array(self._input_trajectory.atom_types)[self._selection]
        )
        unique_elements = np.unique(atom_elements)
        radii = {
            element: ATOMS_DATABASE.get_atom_property(element, "covalent_radius")
            for element in unique_elements
        }
        self._elements = atom_elements
        self._unique_elements = unique_elements
        self._radii = radii
        self.max_distance = 2 * np.max(list(radii.values())) + 0.04

    def internal_distances(
        self, frame_index: int = 0, max_distance: float | None = None
    ) -> dict[tuple[int, int], float]:
        """Calculate distances between pairs of atoms within the specified limit.

        Parameters
        ----------
        frame_index : int, optional
            Trajectory frame for which the distances are calculated, by default 0
        max_distance : float, optional
            Distance limit for bond calculation, in nm, by default None

        Returns
        -------
        dict[tuple[int, int], float]
            Dictionary of {(atom index 1, atom_index 2) : distance} pairs.
        """
        tree = KDTree(self._input_trajectory.coordinates(frame_index, self._selection))
        return tree.sparse_distance_matrix(
            tree, max_distance=max_distance or self.max_distance
        )

    def periodic_distances(
        self, frame_index: int = 0, max_distance: float | None = None
    ) -> Iterable[tuple[int, dict[tuple[int, int], float]]] | None:
        """Calculate the distances between atoms in a periodic box.

        It will create copies of the system translated by unit cell vectors.

        Parameters
        ----------
        frame_index : int, optional
            Trajectory frame for which to calculate distances, by default 0
        max_distance : float, optional
            Distance cutoff in nm, by default None

        Returns
        -------
        None
            If no atoms are selected.

        Yields
        ------
        Iterator[Iterable[tuple[int, dict[tuple[int, int], float]]]]
            Index of box replica and a dictionary of distances.
        """
        unit_cell = self._input_trajectory.unit_cell(frame_index)
        vector_a, vector_b, vector_c = (
            unit_cell.a_vector,
            unit_cell.b_vector,
            unit_cell.c_vector,
        )
        if self._periodic:
            temp_conf = self._input_trajectory.configuration(frame_index)
            temp_conf.fold_coordinates()
            coordinates = temp_conf.coordinates[self._selection]
        else:
            coordinates = self._input_trajectory.coordinates(
                frame_index, self._selection
            )
        if not len(coordinates):
            return None
        tree1 = KDTree(coordinates)
        for num, shift in enumerate(product([-1, 0, 1], repeat=3)):
            if np.allclose(shift, [0, 0, 0]):
                continue
            self._translation_vectors[num] = shift
            offset = shift[0] * vector_a + shift[1] * vector_b + shift[2] * vector_c
            tree2 = KDTree(coordinates + offset.reshape((1, 3)))
            yield (
                num,
                tree1.sparse_distance_matrix(
                    tree2, max_distance=max_distance or self.max_distance
                ),
            )

    def find_bonds(self, frames: list[int] | None = None, tolerance: float = 0.04):
        """Find bonds in the trajectory based on interatomic distances.

        Checks several frames of the trajectory for the presence of atom pairs
        close enough to each other to form chemical bonds. The detected bonds
        are stored internally.

        Parameters
        ----------
        frames : list[int] | None, optional
            Frames for which to check if bonds exist, by default None
        tolerance : float, optional
            Bond length is allowed to exceed the sum of radii by this much, by default 0.04
        """
        if frames is None:
            max_frame = len(self._input_trajectory)
            samples = [0, max_frame - 1] + [max_frame // denom for denom in [2, 3, 5]]
        else:
            samples = frames
        samples = list(np.unique(samples))
        pairs = product(self._unique_elements, repeat=2)
        maxbonds = {
            pair: (self._radii[pair[0]] + self._radii[pair[1]]) + tolerance
            for pair in pairs
        }
        total_max_length = max(maxbonds.values())
        for frame_index in samples:
            distances = self.internal_distances(
                frame_index=frame_index, max_distance=total_max_length
            )
            if self._periodic:
                for _, dist in self.periodic_distances(
                    frame_index=frame_index, max_distance=total_max_length
                ):
                    for key, value in dist.items():
                        distances[key] = min(value, distances.get(key, 99.0))
        bonds = []
        bond_mapping = {atom_number: [] for atom_number in range(len(self._elements))}
        for key, value in distances.items():
            if key[0] == key[1]:
                continue
            element_pair = (self._elements[key[0]], self._elements[key[1]])
            if value > maxbonds[element_pair]:
                continue
            bonds.append(key)
            bond_mapping[key[0]].append(key[1])
        self._bonds = bonds
        self._bond_mapping = bond_mapping
        self._unique_bonds = np.unique(np.sort(bonds, axis=1), axis=0)

    def add_bond_information(self, new_chemical_system: ChemicalSystem):
        new_chemical_system.add_bonds(self._unique_bonds)
        new_chemical_system.find_clusters_from_bonds()
