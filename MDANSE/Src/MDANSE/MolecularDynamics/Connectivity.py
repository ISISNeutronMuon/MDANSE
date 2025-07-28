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

from itertools import product

import numpy as np
from numpy.typing import NDArray
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
        *args,
        trajectory: Trajectory,
        selection: list[int] | None = None,
        **kwargs,
    ):
        self._chemical_system = trajectory.chemical_system
        self._input_trajectory = trajectory
        self._selection = selection
        self._frames = trajectory
        self._unit_cell = self._input_trajectory.configuration(0)
        self._periodic = self._input_trajectory.configuration(0).is_periodic
        self.check_composition(self._chemical_system)
        self._bonds = None
        self._bond_mapping = None
        self._unique_bonds = None
        self._translation_vectors = {}

    def check_composition(self, chemical: ChemicalSystem):
        """Takes the information about the system from an instance
        of the ChemicalSystem class.

        Arguments:
            chemical -- ChemicalSystem instance connected to the trajectory.
        """
        if self._selection is not None:
            atom_elements = [
                self._chemical_system.atom_list[index] for index in self._selection
            ]
        else:
            atom_elements = self._chemical_system.atom_list
        unique_elements = np.unique(atom_elements)
        radii = {
            element: ATOMS_DATABASE.get_atom_property(element, "covalent_radius")
            for element in unique_elements
        }
        self._elements = atom_elements
        self._unique_elements = unique_elements
        self._radii = radii

    def get_coordinates(self, frame_number: int = 0) -> NDArray[np.float64]:
        """Returns a numpy array of the atom positions at the specified
        simulation step (frame).

        Keyword Arguments:
            frame_number -- number of the trajectory frame (default: {0})

        Returns:
            NDArray -- an (N,3) array with the positions of N atoms
        """
        if frame_number < 0 or frame_number >= len(self._frames):
            return None
        if self._selection is not None:
            return self._frames.coordinates(frame_number)[self._selection, :]
        else:
            return self._frames.coordinates(frame_number)

    def internal_distances(
        self, frame_number: int = 0, max_distance: float = 0.2
    ) -> NDArray[np.float64]:
        """Calculates an (N,N) array of interatomic distances SQUARED within
        the simulation box. If there are no periodic boundary conditions,
        the returned array contains ALL the distances in the system.

        Keyword Arguments:
            frame_number -- number of the trajectory frame at which to calculate
                distances (default: {0})

        Returns:
            NDArray -- an (N,N) array of squared distances between all the atom pairs.
        """
        coordinates = self.get_coordinates(frame_number=frame_number)
        if coordinates is None:
            return None
        tree = KDTree(coordinates)
        return tree.sparse_distance_matrix(tree, max_distance=max_distance)

    def periodic_distances(
        self, frame_number: int = 0, max_distance: float = 0.2
    ) -> NDArray[np.float64]:
        """Calculates the distances between the atoms in the simulation box
        and a copy of the simulation box translated by a unit cell vector.
        Only needed if the simulation was run with periodic boundary conditions.

        Keyword Arguments:
            frame_number -- number of the trajectory frame at which to calculate
                distances (default: {0})

        Returns:
            None, if an invalid frame number has been given as input

        Yields:
            NDArray -- an (N,N) array of squared distances between all the atom pairs,
                one for each combination of the unit cell vectors.
        """
        unit_cell = self._input_trajectory.configuration(frame_number).unit_cell
        vector_a, vector_b, vector_c = (
            unit_cell.a_vector,
            unit_cell.b_vector,
            unit_cell.c_vector,
        )
        coordinates = self.get_coordinates(frame_number=frame_number)
        if coordinates is None:
            return None
        tree1 = KDTree(coordinates)
        for num, shift in enumerate(product([-1, 0, 1], repeat=3)):
            if np.allclose(shift, [0, 0, 0]):
                continue
            self._translation_vectors[num] = shift
            offset = shift[0] * vector_a + shift[1] * vector_b + shift[2] * vector_c
            tree2 = KDTree(coordinates + offset.reshape((1, 3)))
            yield num, tree1.sparse_distance_matrix(tree2, max_distance=max_distance)

    def find_bonds(self, frames: list[int] | None = None, tolerance: float = 0.04):
        """Checks several frames of the trajectory for the presence of atom pairs
        close enough to each other to form chemical bonds. The detected bonds
        are stored internally.

        Parameters
        ----------
        frames : Optional[List[int]]
            A list of specific trajectory frames at which to check the bond
            length. Optional (default: {None})
        tolerance : float
            A float constant specifying the tolerance of bond length used
            in bond detection. A bond between two atoms is defined as the
            sum of their covalent radii plus the tolerance in nm.
        """
        if frames is None:
            samples = [len(self._frames) // denom for denom in [2, 3, 4, 5, 6, 7]]
        else:
            samples = frames
        samples = list(np.unique(samples))
        pairs = product(self._unique_elements, repeat=2)
        maxbonds = {
            pair: (self._radii[pair[0]] + self._radii[pair[1]]) + tolerance
            for pair in pairs
        }
        total_max_length = np.max([x for x in maxbonds.values()])
        for _, frame_number in enumerate(samples):
            distances = self.internal_distances(
                frame_number=frame_number, max_distance=total_max_length
            )
            if self._periodic:
                for _, dist in self.periodic_distances(
                    frame_number=frame_number, max_distance=total_max_length
                ):
                    for key, value in dist.items():
                        if key not in distances.keys():
                            distances[key] = value
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

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
