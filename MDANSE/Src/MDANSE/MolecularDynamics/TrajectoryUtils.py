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

import operator
from collections.abc import Iterable
from typing import Union

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error


class MolecularDynamicsError(Error):
    pass


class UniverseAdapterError(Error):
    pass


def elements_from_masses(masses: Iterable[float], tolerance: float = 0.01):
    result = ["X"] * len(masses)
    upper_limit = np.round(masses).astype(int).max()
    all_masses = ATOMS_DATABASE.get_property("atomic_weight")
    for n, mass in enumerate(masses):
        for protons in range(upper_limit):
            possible_matches = ATOMS_DATABASE._atoms_by_atomic_number[protons]
            for match in possible_matches:
                reference_mass = all_masses[match]
                if abs(mass - reference_mass) <= tolerance:
                    result[n] = match
    return result


def atom_index_to_molecule_index(chemical_system: ChemicalSystem) -> list[int]:
    """Returns a list of molecule numbers, per atom. Single
    atoms are assigned the value -1.

    Parameters
    ----------
    chemical_system : ChemicalSystem
        Object describing all the atoms and molecules in the system

    Returns
    -------
    List[int]
        list of molecule numbers, per atom.
    """

    lut = [-1] * len(chemical_system.atom_list)
    last_cluster = 1
    for cluster_name in chemical_system._clusters:
        for cluster in chemical_system._clusters[cluster_name]:
            for atom_index in cluster:
                lut[atom_index] = last_cluster
            last_cluster += 1
    return lut


def find_atoms_in_molecule(
    chemical_system: ChemicalSystem,
    entity_name: str,
    atom_names: list[str],
    indices: bool = False,
) -> list[list[int]]:
    if entity_name not in chemical_system._clusters:
        return []

    result = []
    for index_list in chemical_system._clusters[entity_name]:
        if indices:
            result.append(
                [
                    chemical_system._atom_indices[index]
                    for index in index_list
                    if chemical_system.atom_list[index] in atom_names
                ]
            )
        else:
            result.append(
                [
                    chemical_system.atom_list[index]
                    for index in index_list
                    if chemical_system.atom_list[index] in atom_names
                ]
            )

    return result


def atomic_trajectory(
    config: np.ndarray,
    cell: np.ndarray,
    rcell: np.ndarray,
    *,
    box_coordinates: bool = False,
) -> np.ndarray:
    """For the coordinates of a specific atom, remove all unit cell jumps.

    Parameters
    ----------
    config : np.ndarray
        The coordinates for a specific atoms.
    cell : np.ndarray
        The direct matrices.
    rcell : np.ndarray
        The inverse matrices.
    box_coordinates : bool
        Returns the coordinates in fractional coordinates if true.

    Returns
    -------
    np.ndarray
        The input config but the unit cell jumps removed.

    """
    trajectory = np.einsum("ij,ijk->ik", config, rcell)
    sdxyz = trajectory[1:, :] - trajectory[:-1, :]
    sdxyz -= np.cumsum(np.round(sdxyz), axis=0)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz
    if not box_coordinates:
        trajectory = np.einsum("ij,ijk->ik", trajectory, cell)
    return trajectory
