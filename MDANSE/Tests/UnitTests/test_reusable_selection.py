import os

import pytest

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.MolecularDynamics.Trajectory import Trajectory


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "Converted",
    "short_trajectory_after_changes.mdt",
)
mdmc_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "Converted",
    "Ar_mdmc_h5md.h5",
)
com_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "Converted",
    "com_trajectory.mdt",
)
traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "Converted",
    "2vb1.mdt"
)

@pytest.fixture(scope='module')
def trajectory(request):
   return Trajectory(request.param)


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_select_all(trajectory):
    n_atoms = len(trajectory.chemical_system.atom_list)
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_all'})
    selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(selection) == n_atoms


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_empty_json_string_selects_all(trajectory):
    n_atoms = len(trajectory.chemical_system.atom_list)
    reusable_selection = ReusableSelection()
    reusable_selection.load('{}')
    selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(selection) == n_atoms


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_select_none(trajectory):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_none'})
    selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(selection) == 0


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_inverted_all_is_none(trajectory):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_all'})
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'invert_selection'})
    selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(selection) == 0


def test_json_saving_is_reversible():
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_all'})
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'invert_selection'})
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    json_string_2 = another_selection.convert_to_json()
    assert json_string == json_string_2


@pytest.mark.parametrize("trajectory", [short_traj, mdmc_traj, com_traj], indirect=True)
def test_selection_from_json_is_the_same_as_from_runtime(trajectory):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_all'})
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'invert_selection'})
    selection = reusable_selection.select_in_trajectory(trajectory)
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    selection2 = another_selection.select_in_trajectory(trajectory)
    print(f"original: {reusable_selection.operations}")
    print(f"another: {another_selection.operations}")
    assert selection == selection2


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("element, expected", (
    (["Cu"], 208),
    (["S"], 208),
    (["Sb"], 64),
    (["S", "Sb", "Cu"], 480)
))
def test_select_atoms_selects_by_element(trajectory, element, expected):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={"function_name": "select_atoms",
                                           "atom_types": element})
    selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(selection) == expected
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    loaded_selection = another_selection.select_in_trajectory(trajectory)
    assert len(loaded_selection) == expected


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("index_range, expected", (
    ([15,35], 20),
    ([470,510], 10),
))
def test_select_atoms_selects_by_range(trajectory, index_range, expected):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_atoms', 'index_range': index_range})
    range_selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(range_selection) == expected


@pytest.mark.parametrize("trajectory", [short_traj], indirect=True)
@pytest.mark.parametrize("index_slice, expected", (
    ([150,350,10], 20),
    ([470,510,5], 2),
))
def test_select_atoms_selects_by_slice(trajectory, index_slice, expected):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_atoms', 'index_slice': index_slice})
    range_selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(range_selection) == expected
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    overshoot_selection = another_selection.select_in_trajectory(trajectory)
    assert len(overshoot_selection) == expected


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
@pytest.mark.parametrize("molecule_names, expected", (
    (['H2 O1'], 28746),
    (['C613 H959 N193 O185 S10'], 1960),
))
def test_select_molecules_selects_water(trajectory, molecule_names, expected):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_molecules', 'molecule_names': molecule_names})
    first_selection = reusable_selection.select_in_trajectory(trajectory)
    assert len(first_selection) == expected
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    second_selection = another_selection.select_in_trajectory(trajectory)
    assert len(second_selection) == expected


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
def test_select_molecules_inverted_selects_ions(trajectory):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_molecules', 'molecule_names': ['C613 H959 N193 O185 S10', 'H2 O1']})
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'invert_selection'})
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    non_molecules_selection = another_selection.select_in_trajectory(trajectory)
    assert all([trajectory.chemical_system.atom_list[index] in ['Na', 'Cl'] for index in non_molecules_selection])


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
def test_select_pattern_selects_water(trajectory):
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_pattern', 'rdkit_pattern': "[#8X2;H2](~[H])~[H]"})
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    water_selection = another_selection.select_in_trajectory(trajectory)
    assert len(water_selection) == 28746


@pytest.mark.parametrize("trajectory", [traj_2vb1], indirect=True)
def test_selection_with_multiple_steps(trajectory):
    """This tests if the ReusableSelection can select oxygen only in
    the water molecules. It combines two steps:
    1. water is selected using rdkit pattern matching
    2. oxygen is selected using simple atom type matching; intersection of the selections is applied
    The selection is then saved to a JSON string, loaded from the string and applied to the trajectory.
    """
    reusable_selection = ReusableSelection()
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_pattern', 'rdkit_pattern': "[#8X2;H2](~[H])~[H]"})
    reusable_selection.set_selection(number=None, function_parameters={'function_name': 'select_atoms', 'atom_types': ['O'], 'operation_type': 'intersection'})
    json_string = reusable_selection.convert_to_json()
    another_selection = ReusableSelection()
    another_selection.load(json_string)
    water_oxygen_selection = another_selection.select_in_trajectory(trajectory)
    assert len(water_oxygen_selection) == int(28746/3)
