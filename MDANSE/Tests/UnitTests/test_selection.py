import os

from pathlib import Path
import pytest
import numpy as np

from MDANSE.Framework.AtomSelector.general_selection import select_all, select_none, invert_selection
from MDANSE.Framework.AtomSelector.atom_selection import select_atoms, select_dummy
from MDANSE.Framework.AtomSelector.molecule_selection import select_molecules
from MDANSE.Framework.AtomSelector.group_selection import select_labels, select_pattern
from MDANSE.Framework.AtomSelector.spatial_selection import select_positions, select_sphere
from MDANSE.MolecularDynamics.Trajectory import Trajectory

from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"
traj_2vb1 = CONV_DIR / "2vb1.mdt"
traj_with_dummy = CONV_DIR / "dummy_atoms.mdt"

@pytest.fixture(scope='module')
def trajectory(request):
   return Trajectory(request.param)


@pytest.fixture(scope="module")
def short_trajectory():
    traj_object = Trajectory(short_traj)
    yield traj_object.trajectory
    traj_object.close()


@pytest.fixture(scope="module")
def gromacs_trajectory():
    traj_object = Trajectory(traj_2vb1)
    yield traj_object.trajectory
    traj_object.close()


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_select_all(trajectory):
    n_atoms = len(trajectory.chemical_system.atom_list)
    selection = select_all(trajectory)
    assert len(selection) == n_atoms


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_select_none(trajectory):
    selection = select_none(trajectory)
    assert len(selection) == 0


def test_select_dummy():
    trajectory = Trajectory(traj_with_dummy)
    dummy_selection = select_dummy(trajectory)
    full_selection = select_all(trajectory)
    assert len(full_selection) == 5000
    assert len(dummy_selection) == 500


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_inverted_none_is_all(trajectory):
    none_selection = select_none(trajectory)
    all_selection = select_all(trajectory)
    inverted_none = invert_selection(trajectory, none_selection)
    assert all_selection == inverted_none


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("element, expected", (
    (["Cu"], 208),
    (["S"], 208),
    (["Sb"], 64),
    (["S", "Sb", "Cu"], 480)
))
def test_select_atoms_selects_by_element(trajectory, element, expected):
    s_selection = select_atoms(trajectory, atom_types=element)
    assert len(s_selection) == expected


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("index_range, expected", (
    ([15,35], 20),
    ([470,510], 10),
))
def test_select_atoms_selects_by_range(trajectory, index_range, expected):
    range_selection = select_atoms(trajectory, index_range=index_range)
    assert len(range_selection) == expected


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("index_slice, expected", (
    ([150,350,10], 20),
    ([470,510,5], 2),
))
def test_select_atoms_selects_by_slice(trajectory, index_slice, expected):
    range_selection = select_atoms(trajectory, index_slice=index_slice)
    assert len(range_selection) == expected


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
@pytest.mark.parametrize("molecule_names, expected", (
    (['H2 O1'], 28746),
    (['C613 H959 N193 O185 S10'], 1960),
))
def test_select_molecules(trajectory, molecule_names, expected):
    water_selection = select_molecules(trajectory, molecule_names = molecule_names)
    assert len(water_selection) == expected


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
def test_select_molecules_inverted_selects_ions(trajectory):
    all_molecules_selection = select_molecules(trajectory, molecule_names = ['C613 H959 N193 O185 S10', 'H2 O1'])
    non_molecules_selection = invert_selection(trajectory, all_molecules_selection)
    assert all([trajectory.chemical_system.atom_list[index] in ['Na', 'Cl'] for index in non_molecules_selection])


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
def test_select_pattern_selects_water(trajectory):
    water_selection = select_pattern(trajectory, rdkit_pattern="[#8X2;H2](~[H])~[H]")
    assert len(water_selection) == 28746


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("lower_limit, upper_limit, expected", (
    ([0.5, 0.5, 0.5], [0.7, 0.7, 0.7], {59}),
    (None, [0.2, 0.2, 0.2], {46}),
    ([1.8, 1.8, 1.8], None, {453}),
))
def test_select_positions(trajectory, lower_limit, upper_limit, expected):
    cube_selection = select_positions(trajectory,
                                      position_minimum = lower_limit,
                                      position_maximum = upper_limit)
    assert cube_selection == expected


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
def test_select_sphere(trajectory):
    sphere_selection = select_sphere(trajectory,
                                      sphere_centre = 0.6*np.ones(3),
                                      sphere_radius = 0.2)
    assert sphere_selection == {19, 17, 59, 15}
