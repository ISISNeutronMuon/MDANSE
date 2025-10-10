import numpy as np
from scipy.spatial import KDTree
import pytest

from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.Framework.Jobs.SolventAccessibleSurface import (
    compare_trees,
    solvent_accessible_surface,
)

N_SPHERE_POINTS = 500


@pytest.fixture(scope="module")
def sphere_tree():
    sphere = generate_sphere_points(N_SPHERE_POINTS)
    sphere_tree = KDTree(sphere)
    return sphere_tree


@pytest.fixture(scope="module")
def atom_tree():
    atoms = np.array([[1, 0, 0]])
    atom_tree = KDTree(atoms)
    return atom_tree


def test_compare_trees_blocks_nothing(sphere_tree, atom_tree):
    free_sphere_points = compare_trees(
        sphere_tree,
        atom_tree,
        set(range(N_SPHERE_POINTS)),
        np.array([0]),
        2.0,
        0.0,
        0.0,
    )
    assert len(free_sphere_points) == N_SPHERE_POINTS


def test_compare_trees_blocks_everything(sphere_tree, atom_tree):
    free_sphere_points = compare_trees(
        sphere_tree,
        atom_tree,
        set(range(N_SPHERE_POINTS)),
        np.array([2.0]),  # van der Waals radii of atoms
        2.5,  # max distance
        0.0,  # min distance
        0.1,  # probe particle radius
    )
    assert len(free_sphere_points) == 0


def test_compare_trees_blocks_half(sphere_tree, atom_tree):
    free_sphere_points = compare_trees(
        sphere_tree,
        atom_tree,
        set(range(N_SPHERE_POINTS)),
        np.array([1.315]),  # van der Waals radii of atoms
        2.5,  # max distance
        0.0,  # min distance
        0.1,  # probe particle radius
    )
    print(len(free_sphere_points))
    assert len(free_sphere_points) == int(N_SPHERE_POINTS / 2)


def test_sas_blocked_is_positive_for_same_atoms():
    coords = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1],
        ]
    )
    all_indices = np.arange(8)
    selected_indices = {0}
    grouping_indices = np.ones(8)
    vdw_radii = 0.5 * np.ones(8)
    sphere_points = generate_sphere_points(N_SPHERE_POINTS)
    probe_radius = 0.5
    results = solvent_accessible_surface(
        coords,
        all_indices,
        selected_indices,
        grouping_indices,
        vdw_radii,
        sphere_points,
        probe_radius,
    )
    assert results[0] > 0.0
    assert all(res > 0 for res in results[1].values())


def test_sas_blocked_is_nonnegative_for_different_atoms():
    coords = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0],
            [1, 1, 1],
        ]
    )
    all_indices = np.arange(8)
    selected_indices = {0}
    grouping_indices = np.arange(8) + 1
    vdw_radii = 0.5 * np.ones(8)
    sphere_points = generate_sphere_points(N_SPHERE_POINTS)
    probe_radius = 0.5
    results = solvent_accessible_surface(
        coords,
        all_indices,
        selected_indices,
        grouping_indices,
        vdw_radii,
        sphere_points,
        probe_radius,
    )
    print(results[0])
    print(results[1])
    assert results[0] > 0.0
    assert all(res >= 0 for res in results[1].values())
