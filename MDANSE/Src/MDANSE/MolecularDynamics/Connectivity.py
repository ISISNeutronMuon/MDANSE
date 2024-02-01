# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/MolecularDynamics/Connectivity.py
# @brief     A simple molecule detection tool.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Maciej Bartkowiak
#
# **************************************************************************

from itertools import product
from typing import List, Dict

import numpy as np
from numpy.typing import NDArray

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class Connectivity:
    """This class calculates the distances between atoms in a trajectory,
    and identifies potential molecules based on distances alone.
    """

    def __init__(self, *args, trajectory: Trajectory = None, **kwargs):
        self._chemical_system = trajectory.chemical_system
        self._frames = trajectory
        self._unit_cell = self._chemical_system.configuration
        self._periodic = self._chemical_system.configuration.is_periodic
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
        atom_elements = [atom.symbol for atom in chemical.atoms]
        unique_elements = np.unique(atom_elements)
        radii = {
            element: ATOMS_DATABASE[element]["covalent_radius"]
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
        return self._frames.coordinates(frame_number)

    def internal_distances(self, frame_number: int = 0) -> NDArray[np.float64]:
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
        lhs = coordinates.reshape((len(coordinates), 1, 3))
        rhs = coordinates.reshape((1, len(coordinates), 3))
        difference = lhs - rhs
        distance = np.sum(difference**2, axis=2)
        return distance

    def periodic_distances(self, frame_number: int = 0) -> NDArray[np.float64]:
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
        unit_cell = self._chemical_system.configuration.unit_cell
        vector_a, vector_b, vector_c = (
            unit_cell.a_vector,
            unit_cell.b_vector,
            unit_cell.c_vector,
        )
        coordinates = self.get_coordinates(frame_number=frame_number)
        if coordinates is None:
            return None
        lhs = coordinates.reshape((len(coordinates), 1, 3))
        rhs = coordinates.reshape((1, len(coordinates), 3))
        for num, shift in enumerate(product([-1, 0, 1], repeat=3)):
            if np.allclose(shift, [0, 0, 0]):
                continue
            self._translation_vectors[num] = shift
            offset = shift[0] * vector_a + shift[1] * vector_b + shift[2] * vector_c
            difference = lhs - rhs + offset
            distance = np.sum(difference**2, axis=2)
            yield num, distance

    def find_bonds(self, frames: List[int] = None, tolerance: float = 0.2):
        """Checks several frames of the trajectory for the presence of atom pairs
        close enough to each other to form chemical bonds. The detected bonds
        are stored internally.

        Keyword Arguments:
            frames -- a list of specific trajectory frames at which to check the bond
                length. Optional (default: {None})
            tolerance -- A float constant specifying the tolerance of bond length used
                in bond detection. 0.2 means that distance between atoms may be
                up to 20% larger than the nominal length of the bond (default: {0.2})
        """
        if frames is None:
            samples = [len(self._frames) // denom for denom in [2, 3, 4, 5]]
        else:
            samples = frames
        bonds = []
        pairs = product(self._unique_elements, repeat=2)
        maxbonds = {
            pair: ((self._radii[pair[0]] + self._radii[pair[1]]) * (1.0 + tolerance))
            ** 2
            for pair in pairs
        }
        max_distance_array = np.zeros((len(self._elements), len(self._elements)))
        connection_array = np.zeros(
            (len(self._elements), len(self._elements)), dtype=bool
        )
        pair_array = np.array(
            [[(x, y) for x in self._elements] for y in self._elements]
        )
        for pair, maxlength in maxbonds.items():
            max_distance_array[
                np.where(
                    np.logical_and(
                        pair_array[:, :, 0] == pair[0], pair_array[:, :, 1] == pair[1]
                    )
                )
            ] = maxlength
        for nstep, frame_number in enumerate(samples):
            distances = [(None, self.internal_distances(frame_number=frame_number))]
            if self._periodic:
                for num, dist in self.periodic_distances(frame_number=frame_number):
                    distances.append((num, dist))
            for ndist, disttuple in enumerate(distances):
                vecnum, dist = disttuple
                result = dist < max_distance_array
                if ndist == 0:
                    # internal distances: bond with self possible, and wrong
                    result = np.logical_and(
                        result,
                        dist > 1e-3,
                    )
                connection_array = np.logical_or(connection_array, result)
        first, second = np.where(connection_array)
        bonds = np.column_stack([first, second])
        bond_mapping = {atom_number: [] for atom_number in range(len(self._elements))}
        for pair in bonds:
            bond_mapping[pair[0]].append(pair[1])
        self._bonds = bonds
        self._bond_mapping = bond_mapping
        self._unique_bonds = np.unique(np.sort(bonds, axis=1), axis=0)

    def find_molecules(self, tolerance: float = 0.2):
        """Uses the internal list of bonds to find atoms that belong to the same
        molecules. The grouping of atoms is saved internally.
        """
        if self._bond_mapping is None:
            self.find_bonds(tolerance=tolerance)

        def recursive_walk(
            number: int, bond_mapping: Dict[int, int], atom_pool: List[int]
        ):
            """Returns a list of atoms connected by bonds to the input atom.
            Called recursively in order to find the entire molecule.

            Arguments:
                number -- number (index) of the starting atom on the atom list.
                bond_mapping -- dictionary of the interatomic connections,
                    determined using the find_bonds method.
                atom_pool -- a list of all the atom numbers, each atom to be used
                    once only. Once an atom number has been assigned to a molecule,
                    it will also be removed from this list.

            Returns:
                List[int] -- a list of atom numbers (indices)
            """
            connected_atoms = [number]
            for at_number in bond_mapping[number]:
                if at_number in atom_pool:
                    connected_atoms.append(at_number)
                    atom_pool.pop(atom_pool.index(at_number))
                    connected_atoms += recursive_walk(
                        at_number, bond_mapping, atom_pool
                    )
            return connected_atoms

        molecules = []
        atom_pool = list(range(len(self._elements)))
        while len(atom_pool):
            new_molecule = recursive_walk(
                atom_pool.pop(), self._bond_mapping, atom_pool
            )
            molecules.append(list(np.unique(new_molecule)))
        self._molecules = molecules

    def add_bond_information(self):
        for bond in self._unique_bonds:
            ind1, ind2 = bond
            at1, at2 = (
                self._chemical_system.atoms[bond[0]],
                self._chemical_system.atoms[bond[1]],
            )
            at1.bonds.append(at2)
            at2.bonds.append(at1)
            self._chemical_system._bonds.append((ind1, ind2))

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
