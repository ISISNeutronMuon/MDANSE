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

from itertools import pairwise
from typing import TYPE_CHECKING

import numpy as np
from more_itertools import chunked_even

if TYPE_CHECKING:
    from MDANSE.MolecularDynamics.Trajectory import Trajectory

CHUNK_SIZE_LIMIT = 2**29  # 512 MB memory limit per process for now

from MDANSE.util_types import FloatArray


class MolecularDynamicsError(Exception):
    pass


class UniverseAdapterError(Exception):
    pass


def atomic_trajectory(
    config: FloatArray,
    cell: FloatArray,
    rcell: FloatArray,
    *,
    box_coordinates: bool = False,
) -> FloatArray:
    """For the coordinates of a specific atom, remove all unit cell jumps.

    Parameters
    ----------
    config : FloatArray
        The coordinates for a specific atoms.
    cell : FloatArray
        The direct matrices.
    rcell : FloatArray
        The inverse matrices.
    box_coordinates : bool
        Returns the coordinates in fractional coordinates if true.

    Returns
    -------
    FloatArray
        The input config but the unit cell jumps removed.

    """
    trajectory = np.einsum("ij,ijk->ik", config, rcell)
    sdxyz = trajectory[1:, :] - trajectory[:-1, :]
    sdxyz -= np.cumsum(np.round(sdxyz), axis=0)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz
    if not box_coordinates:
        trajectory = np.einsum("ij,ijk->ik", trajectory, cell)
    return trajectory


def atomic_trajectory_many(
    config: FloatArray,
    cell: FloatArray,
    rcell: FloatArray,
    *,
    box_coordinates: bool = False,
) -> FloatArray:
    """For the coordinates of a specific atom, remove all unit cell jumps.

    Parameters
    ----------
    config : FloatArray
        The coordinates for a specific atoms.
    cell : FloatArray
        The direct matrices.
    rcell : FloatArray
        The inverse matrices.
    box_coordinates : bool
        Returns the coordinates in fractional coordinates if true.

    Returns
    -------
    FloatArray
        The input config but the unit cell jumps removed.

    """
    # i is time, j is the XYZ coordinate
    trajectory = np.einsum("inj,ijk->ink", config, rcell)
    sdxyz = trajectory[1:, :] - trajectory[:-1, :]
    sdxyz -= np.cumsum(np.round(sdxyz), axis=0)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz
    if not box_coordinates:
        trajectory = np.einsum("inj,ijk->ink", trajectory, cell)
    return trajectory


def group_atom_indices(
    traj_instance: Trajectory,
    n_proc: int = 1,
    memory_scale_factor: int = 10,
    size_limit: int = CHUNK_SIZE_LIMIT,
) -> list[list[int]]:
    """Create groups of atom indices coaligned with the chunk size in the input file.

    This function is meant to group indices so that a single process loads data
    from a single chunk per frame. Additionally, indices will be split into smaller
    sets if a process is expected to use more memory than the specified limits, or
    if there are less index sets than there are worker processes.

    Typically, the memory requirements will be proportional to the size of the
    input array, but larger. For example, DISF analysis allocates an array
    of the size of N_ATOMSxN_VECTORS, which means that the worker process
    will need significantly more memory that the size of the input coordinate
    array.

    Parameters
    ----------
    traj_instance : Trajectory
        The current input trajectory.
    n_proc : int, optional
        Number of available CPU cores or worker processes, by default 1
    memory_scale_factor : int, optional
        Multiplier of the expected memory requirements of the job, by default 10
    size_limit : int, optional
        Limit of memory per worker process, by default CHUNK_SIZE_LIMIT

    Returns
    -------
    list[set[int]]
        List of atom index set, each set containing indices from a single HDF5 chunk
    """
    selected_indices = set(traj_instance.atom_indices)
    total_dimensions = traj_instance.variable("position").shape
    chunk_size = traj_instance.chunk_size(array_name="position")
    if chunk_size < 0:
        max_chunk_size = size_limit // (
            total_dimensions[0] * 3 * 8 * memory_scale_factor
        )
        chunk_limits = np.array([0, total_dimensions[1]])
    else:
        predicted_memory = (
            total_dimensions[0] * chunk_size * 3 * 8 * memory_scale_factor
        )
        downscale_factor = np.ceil(predicted_memory / size_limit)
        max_chunk_size = chunk_size // downscale_factor
        chunk_limits = np.concatenate(
            [np.arange(0, total_dimensions[1], chunk_size), [total_dimensions[1]]]
        )
    min_chunk_count = n_proc
    initial_sets = [
        sorted(selected_indices.intersection(range(*chunk_block)))
        for chunk_block in pairwise(chunk_limits)
    ]
    initial_sets = [index_set for index_set in initial_sets if len(index_set)]
    return balance_index_groups(
        initial_sets, max_size=int(max_chunk_size), min_count=min_chunk_count
    )


def split_index_sets(index_sets: list[set[int]], max_size: int) -> list[set[int]]:
    """Check the size of each atom index set and split those exceeding the size limit.

    Parameters
    ----------
    index_sets : list[set[int]]
        List of atom index sets to be used by worker processes.
    max_size : int
        Maximum number of atoms per set.

    Returns
    -------
    list[set[int]]
        List of index sets after splitting into smaller sets.
    """
    return [
        chunk for ind_set in index_sets for chunk in chunked_even(ind_set, max_size)
    ]


def balance_index_groups(
    index_sets: list[set[int]], max_size: int, min_count: int
) -> list[set[int]]:
    """Iteratively split atom index sets until the optimal size has been reached.

    Parameters
    ----------
    index_sets : list[set[int]]
        List of atom index set, one set per analysis step.
    max_size : int
        Maximum number of atoms per set.
    min_count : int
        Minimum number of sets needed by the analysis.

    Returns
    -------
    list[set[int]]
        List of index sets after splitting into smaller sets.
    """
    while any(len(ind_set) > max_size for ind_set in index_sets):
        index_sets = split_index_sets(index_sets, max_size)
        if len(index_sets) < min_count:
            max_size = 3 * max_size // 4
    return index_sets
