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

import numpy as np
from numpy.typing import NDArray

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData


class Connectivity:
    """This class calculates the distances between atoms in a trajectory,
    and identifies potential molecules based on distances alone.
    """

    def __init__(self, *args, trajectory: HDFTrajectoryInputData = None, **kwargs):
        self._trajectory_file = trajectory
        self._chemical_system = trajectory.chemical_system
        self._frames = trajectory.trajectory
        self._unit_cell = self._chemical_system.configuration
        self._periodic = self._chemical_system.configuration.is_periodic
        self.check_composition(self._chemical_system)

    def check_composition(self, chemical: ChemicalSystem):
        atom_elements = [atom.symbol for atom in chemical.atoms]
        unique_elements = np.unique(atom_elements)
        radii = {
            element: ATOMS_DATABASE[element]["covalent_radius"]
            for element in unique_elements
        }
        self._elements = atom_elements
        self._unique_elements = unique_elements
        self._radii = radii

    def get_coordinates(self, frame_number: int = 0):
        if frame_number < 0 or frame_number >= len(self._frames):
            return None
        return self._frames.coordinates(frame_number)

    def internal_distances(self, frame_number: int = 0) -> NDArray[np.float64]:
        coordinates = self.get_coordinates(frame_number=frame_number)
        if coordinates is None:
            return None
        lhs = coordinates.reshape((len(coordinates), 1, 3))
        rhs = coordinates.reshape((1, len(coordinates), 3))
        difference = lhs - rhs
        distance = np.sum(difference**2, axis=2)
        return distance

    def periodic_distances(self, frame_number: int = 0) -> NDArray[np.float64]:
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
        for shift in product([-1, 0, 1], repeat=3):
            if np.allclose(shift, [0, 0, 0]):
                pass
            offset = shift[0] * vector_a + shift[1] * vector_b + shift[2] * vector_c
            print(offset)
            difference = lhs - rhs + offset
            distance = np.sum(difference**2, axis=2)
            yield distance

    def find_bonds(self, frames=None, tolerance=0.2):
        if frames is None:
            samples = [len(self._frames) // denom for denom in [2, 3, 4, 5]]
        else:
            samples = frames
        bonds = []
        pairs = product(self._unique_elements, repeat=2)
        maxbonds = {
            pair: ((self._radii[pair[0]] + self._radii[pair[1]]) * (1.0 + tolerance))**2
            for pair in pairs
        }
        connected = np.empty(
            [len(self._elements), len(self._elements), len(samples)], dtype=bool
        )
        print(f"Shape of connected: {connected.shape}")
        for pair, maxlength in maxbonds.items():
            vertical = np.where(self._elements == pair[0])
            horizontal = np.where(self._elements == pair[1])
            print(f"Pair is {pair}")
            print(f"Allowed bond length: {maxlength}")
            for nstep, frame_number in enumerate(samples):
                distances = [self.internal_distances(frame_number=frame_number)]
                # if self._periodic:
                #     for dist in self.periodic_distances(frame_number=frame_number):
                #         distances.append(dist)
                for dist in distances:
                    print(f"Min. distance: {dist.min()}, mean distance: {dist.mean()}")
                    temp = dist[vertical, horizontal] <= maxlength
                    connected[vertical, horizontal, nstep] = np.logical_or(
                        connected[vertical, horizontal, nstep], temp
                    )
            print(f"Sum of connected is now {connected.sum()}")
        result = np.sum(connected, axis=2)
        print(f"Shape of result: {connected.shape}")
        first, second = np.where(result > 0)
        for x in range(len(first)):
            bonds.append((first[x], second[x]))
        return bonds

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
