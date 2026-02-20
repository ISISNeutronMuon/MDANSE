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
import numpy.typing as npt
from scipy.spatial import KDTree

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import padded_coordinates
from MDANSE.MolecularDynamics.Trajectory import Trajectory


def distance_calculation(
    coordinates: npt.NDArray[float], max_distance: float, worker_limit: int = -1
) -> tuple[npt.NDArray[float], npt.NDArray[int], npt.NDArray[int], npt.NDArray[float]]:
    """Calculate distances between atoms in the input array.

    KDTree is used to calculate distances, and only distances within
    the max_distance cutoff are considered.

    This calculation is typically used for detecting chemical bonds between
    atoms based on interatomic distances.

    Parameters
    ----------
    coordinates : npt.NDArray[float]
        An (N,3) array of atom coordinates.
    max_distance : float
        The largest distance to be considered in the calculation.
    worker_limit : int, optional
        Number of CPU cores to use, where -1 uses all available cores, by default -1

    Returns
    -------
    tuple[npt.NDArray[float], npt.NDArray[int], npt.NDArray[int], npt.NDArray[float]]
        Distance array, Indices of first atom, Indices of second atom, Coordinate difference array.
    """
    tree = KDTree(coordinates)
    contacts = tree.query_ball_point(coordinates, max_distance, workers=worker_limit)

    # generate indexes of all pairs of points in close contact
    # e.g. js = [0, 0, 0, ...] and ks = [1, 2, 4, ...]
    # so that pairs (0, 1), (0, 2), (0, 4), ... are in close contact
    n_contacts = np.fromiter((len(i) for i in contacts), dtype=int)
    mask = n_contacts > 0
    js = np.repeat(np.nonzero(mask)[0], n_contacts[mask])
    ks = np.concatenate([contacts[i] for i in np.nonzero(mask)[0]])

    mask = js < ks
    js = js[mask]
    ks = ks[mask]
    diff = coordinates[js] - coordinates[ks]
    dist = np.sum(diff * diff, axis=1)
    return dist, js, ks, diff


class Connectivity:
    """This class calculates the distances between atoms in a trajectory,
    and identifies potential molecules based on distances alone.
    """

    def __init__(
        self,
        trajectory: Trajectory,
        selection: list[int] | None = None,
        parallel_workers: int | None = None,
    ):
        self.worker_limit = parallel_workers or -1
        self._input_trajectory = trajectory
        self._selection = selection or trajectory._selection or trajectory.atom_indices
        self._periodic = self._input_trajectory.configuration(0).is_periodic
        self.check_composition()
        self._unique_bonds = []
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

    def total_distances_sq(
        self, frame_index: int = 0, max_distance: float | None = None
    ) -> dict[tuple[int, int], float]:
        """Calculate squared distances between pairs of atoms within the specified limit.

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
        coordinates, atom_indices = padded_coordinates(
            self._input_trajectory.coordinates(frame_index, self._selection),
            self._input_trajectory.unit_cell(frame_index),
            1.1 * max_distance,
        )
        dist, js, ks, diff = distance_calculation(
            coordinates,
            max_distance or self.max_distance,
            worker_limit=self.worker_limit,
        )

        return {
            (atom_indices[js[common_index]], atom_indices[ks[common_index]]): dist[
                common_index
            ]
            for common_index in range(len(diff))
        }

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
            samples = [0, max_frame - 1]
        else:
            samples = frames
        samples = list(np.unique(samples))
        pairs = product(self._unique_elements, repeat=2)
        maxbonds = {
            pair: (self._radii[pair[0]] + self._radii[pair[1]]) + tolerance
            for pair in pairs
        }
        maxbonds_sq = {key: value**2 for key, value in maxbonds.items()}
        total_max_length = max(maxbonds.values())
        bonds = []
        for frame_index in samples:
            distances_sq = self.total_distances_sq(
                frame_index=frame_index, max_distance=total_max_length
            )
            for key, value in distances_sq.items():
                element_pair = (self._elements[key[0]], self._elements[key[1]])
                if value > maxbonds_sq[element_pair]:
                    continue
                bonds.append(key)
        if bonds:
            self._unique_bonds = np.unique(np.sort(bonds, axis=1), axis=0)

    def add_bond_information(self, new_chemical_system: ChemicalSystem):
        new_chemical_system.add_bonds(self._unique_bonds)
        new_chemical_system.find_clusters_from_bonds()
