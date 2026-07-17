#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

import numpy as np
import pytest

from MDANSE.MolecularDynamics.TrajectoryUtils import (
    balance_index_groups,
    get_natoms_per_step,
    split_index_sets,
    split_selected_atoms,
)


@pytest.fixture(scope="module")
def selected_indices():
    all_indices = set(range(20000))
    all_indices -= set(range(400, 600))
    all_indices -= set(range(10000, 20000, 7))
    return all_indices


@pytest.mark.parametrize("chunk_size", [-1, 128, 2000])
@pytest.mark.parametrize(
    "trajectory_size", [(500, 20000), (10000, 20000), (100000, 20000)]
)
@pytest.mark.parametrize("scale_factor", [1, 10, 1000])
@pytest.mark.parametrize("size_limit", [2**24, 2**28, 2**32])
def test_natoms_per_step_is_not_zero(
    chunk_size, trajectory_size, scale_factor, size_limit
):
    n_atoms_per_step = get_natoms_per_step(
        chunk_size, trajectory_size, scale_factor, size_limit
    )
    assert n_atoms_per_step > 0


@pytest.mark.parametrize("chunk_size", [-1, 128, 2000])
@pytest.mark.parametrize(
    "trajectory_size", [(500, 20000), (10000, 20000), (100000, 20000)]
)
@pytest.mark.parametrize("scale_factor", [1, 10, 1000])
@pytest.mark.parametrize("size_limit", [2**24, 2**28, 2**32])
def test_groups_are_not_empty(
    selected_indices, chunk_size, trajectory_size, scale_factor, size_limit
):
    n_atoms_per_step = get_natoms_per_step(
        chunk_size, trajectory_size, scale_factor, size_limit
    )
    grouped_indices = split_selected_atoms(
        selected_indices, chunk_size, trajectory_size, n_atoms_per_step, 8
    )
    assert all(len(grp) for grp in grouped_indices)
    assert all(len(grp) <= n_atoms_per_step for grp in grouped_indices)


@pytest.mark.parametrize("max_size", [1000, 100, 10, 1])
@pytest.mark.parametrize("min_count", [1, 10, 100, 1000])
def test_group_balancing_reaches_target(selected_indices, max_size, min_count):
    total_index_count = len(np.ravel(selected_indices))
    final_groups = balance_index_groups([selected_indices], max_size, min_count)
    assert all(len(grp) for grp in final_groups)
    assert all(len(grp) <= max_size for grp in final_groups)
    assert len(final_groups) >= min(total_index_count, min_count)
