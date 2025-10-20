from __future__ import annotations

from collections.abc import Sequence

import h5py
import numpy as np
import pytest
from scipy.spatial import KDTree
from test_helpers.paths import CONV_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.SolventAccessibleSurface import (
    compare_trees,
    create_type_mapping,
    identify_loose_atoms,
    make_grouping_indices,
    solvent_accessible_surface,
)
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.MolecularDynamics.Trajectory import Trajectory

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


@pytest.fixture(scope="module")
def sas_co2_atoms(tmp_path_factory):
    """SAS analysis results for atom grouping and very small probe particle."""
    temp_name = tmp_path_factory.mktemp("data") / "output_sas_atoms"
    out_file = temp_name.with_suffix(".mda")
    parameters = {
        "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_dummy", "operation_type": "difference"}, "2": {"function_name": "select_atoms", "index_list": [0, 1, 2], "operation_type": "intersection"}}',  # atom_selection
        "frames": [0, 3, 1],  # frames
        "grouping_level": "atom",  # grouping_level
        "n_sphere_points": str(N_SPHERE_POINTS),  # n_sphere_points
        "output_files": (temp_name, ["MDAFormat"], "no logs"),  # output_files
        "probe_radius": "0.0001",  # probe_radius
        "calculate_blocked_surface": True,
        "running_mode": ("single-core",),  # running_mode
        "trajectory": CONV_DIR / "fake_co2_molecules.mdt",  # trajectory
    }
    solventaccessiblesurface = IJob.create("SolventAccessibleSurface")
    solventaccessiblesurface.run(parameters, status=False, prog_bar=False)
    with h5py.File(out_file) as results:
        sas_values = {"total": results["sas/total"][:], "free": results["sas/free"][:]}
    return sas_values


@pytest.fixture(scope="module")
def sas_co2_molecules(tmp_path_factory):
    """SAS analysis results for molecule grouping and very small probe particle."""
    temp_name = tmp_path_factory.mktemp("data") / "output_sas_molecules"
    out_file = temp_name.with_suffix(".mda")
    parameters = {
        "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_dummy", "operation_type": "difference"}, "2": {"function_name": "select_atoms", "index_list": [0, 1, 2], "operation_type": "intersection"}}',  # atom_selection
        "frames": [0, 3, 1],  # frames
        "grouping_level": "molecule",  # grouping_level
        "n_sphere_points": str(N_SPHERE_POINTS),  # n_sphere_points
        "output_files": (temp_name, ["MDAFormat"], "no logs"),  # output_files
        "probe_radius": "0.0001",  # probe_radius
        "calculate_blocked_surface": True,
        "running_mode": ("single-core",),  # running_mode
        "trajectory": CONV_DIR / "fake_co2_molecules.mdt",  # trajectory
    }
    solventaccessiblesurface = IJob.create("SolventAccessibleSurface")
    solventaccessiblesurface.run(parameters, status=False, prog_bar=False)
    with h5py.File(out_file) as results:
        sas_values = {"total": results["sas/total"][:], "free": results["sas/free"][:]}
    return sas_values


@pytest.fixture(scope="module")
def atoms_in_molecule():
    traj_instance = Trajectory(CONV_DIR / "fake_co2_molecules.mdt")
    molecule_atoms, _ = identify_loose_atoms(traj_instance, "molecule")
    traj_instance.close()
    return molecule_atoms


@pytest.fixture(scope="module")
def loose_atoms():
    traj_instance = Trajectory(CONV_DIR / "fake_co2_molecules.mdt")
    _, loose_atoms = identify_loose_atoms(traj_instance, "atom")
    traj_instance.close()
    return loose_atoms


def capsule_surface(radii: Sequence[float], length: float) -> float:
    """Calculate the approximate surface of a linear molecule.

    The approximation assumes the molecule to be a cylinder terminated
    by two hemispheres. The radius is the arithmetic mean of the radii
    of the component atoms.

    Parameters
    ----------
    radius : Sequence[float]
        All the radii of the atoms in the molecule.
    length : float
        Distance from the first to the last atom of the molecule.

    Returns
    -------
    float
        Surface area of the molecule.
    """
    radius = np.mean(radii)
    length = 2 * 0.116
    sphere_surface = 4 * np.pi * radius**2
    cylinder_surface = 2 * np.pi * radius * length
    return sphere_surface + cylinder_surface


def test_compare_trees_blocks_nothing(sphere_tree, atom_tree):
    """For van der Waals radius of 0, the atoms don't block any volume."""
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
    """For van der Waals radius of 20 Angstrom, the atom blocks the entire sphere."""
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
    """A value of van der Waals radius can be found that blocks half the sphere points."""
    free_sphere_points = compare_trees(
        sphere_tree,
        atom_tree,
        set(range(N_SPHERE_POINTS)),
        np.array([1.315]),  # van der Waals radii of atoms
        2.5,  # max distance
        0.0,  # min distance
        0.1,  # probe particle radius
    )
    assert len(free_sphere_points) == int(N_SPHERE_POINTS / 2)


def test_identify_loose_atoms_atom_grouping():
    traj_instance = Trajectory(CONV_DIR / "fake_co2_molecules.mdt")
    molecule_atoms, loose_atoms = identify_loose_atoms(traj_instance, "atom")
    traj_instance.close()
    assert len(molecule_atoms) == 0
    for atom in ["O", "C"]:
        assert atom in loose_atoms


def test_identify_loose_atoms_atom_grouping():
    traj_instance = Trajectory(CONV_DIR / "fake_co2_molecules.mdt")
    molecule_atoms, loose_atoms = identify_loose_atoms(traj_instance, "molecule")
    traj_instance.close()
    assert len(loose_atoms) == 0
    for atom in ["O", "C"]:
        assert atom in molecule_atoms["C1_O2"]


def test_create_type_mapping_atom_grouping():
    type_mapping, grouping_keys = create_type_mapping(
        ["C", "O", "O", "C", "O", "O"],
        "atom",
    )
    for atom in ["C", "O"]:
        assert atom in type_mapping
    for key, value in type_mapping.items():
        assert grouping_keys[value] == key


def test_create_type_mapping_molecule_grouping(atoms_in_molecule):
    type_mapping, grouping_keys = create_type_mapping(
        ["C", "O", "O", "C", "O", "O"],
        "molecule",
        ["C1_O2"],
        atoms_in_molecule=atoms_in_molecule,
    )
    for atom in ["C", "O"]:
        assert atom in type_mapping
    for key, value in type_mapping.items():
        assert grouping_keys[value] == key


def test_make_grouping_indices_atom_grouping():
    selection = list(range(3))
    grouping_indices = make_grouping_indices(
        list(range(6)),
        selection,
        ["C", "O", "O", "C", "O", "O"],
        {"O": 1, "C": 2},
        "atom",
        {"C1_O2": [[0, 1, 2], [3, 4, 5]]},
    )
    np.testing.assert_allclose(grouping_indices[selection], 0)
    np.testing.assert_allclose(grouping_indices, [0, 0, 0, 2, 1, 1])


def test_make_grouping_indices_molecule_grouping():
    selection = list(range(3))
    grouping_indices = make_grouping_indices(
        list(range(6)),
        selection,
        ["C", "O", "O", "C", "O", "O"],
        {"O": 1, "C": 2, "<C1_O2>/O": 3, "<C1_O2>/C": 4},
        "molecule",
        {"C1_O2": [[0, 1, 2], [3, 4, 5]]},
    )
    print(grouping_indices)
    np.testing.assert_allclose(grouping_indices[selection], 0)
    np.testing.assert_allclose(grouping_indices, [0, 0, 0, 4, 3, 3])


def test_make_grouping_indices_molecule_grouping_incomplete_selection():
    selection = list(range(2))
    grouping_indices = make_grouping_indices(
        list(range(6)),
        selection,
        ["C", "O", "O", "C", "O", "O"],
        {"O": 1, "C": 2, "<C1_O2>/O": 3, "<C1_O2>/C": 4},
        "molecule",
        {"C1_O2": [[0, 1, 2], [3, 4, 5]]},
    )
    print(grouping_indices)
    np.testing.assert_allclose(grouping_indices[selection], 0)
    np.testing.assert_allclose(grouping_indices, [0, 0, 1, 4, 3, 3])


def test_sas_blocked_is_positive_for_same_atoms():
    """Make sure the blocked surface is never negative if all atoms are the same type."""
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
        calculate_blocking=True,
    )
    assert results[0] > 0.0
    assert all(res > 0 for res in results[2].values())


def test_sas_blocked_is_nonnegative_for_different_atoms():
    """Make sure the blocked surface is never negative when all the atoms are different types."""
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
        calculate_blocking=True,
    )
    assert results[0] > 0.0
    assert all(res >= 0 for res in results[2].values())


@pytest.mark.parametrize("key_name", ("total", "free"))
def test_same_sas_for_atoms_and_molecules(key_name, sas_co2_atoms, sas_co2_molecules):
    """Check that grouping does not change the total and free surface results."""
    np.testing.assert_allclose(sas_co2_atoms[key_name], sas_co2_molecules[key_name])


def test_capsule_volume(sas_co2_atoms):
    """Check that the surface from SAS analysis is close to a simplified model calculation."""
    radii = [0.17, 0.152, 0.152]
    length = 2 * 0.116
    total_co2_approximated = capsule_surface(radii, length)
    print(total_co2_approximated, "nm^2")
    np.testing.assert_allclose(
        total_co2_approximated, sas_co2_atoms["total"], rtol=0.01, atol=0.01
    )
