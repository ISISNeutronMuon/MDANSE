import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.AtomSelector.selector import Selector


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


def test_selector_returns_all_atom_idxs(protein_trajectory):
    selector = Selector(protein_trajectory)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714


def test_selector_returns_all_atom_idxs_with_all_and_sulfurs_selected(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = True
    selector.settings["element"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714


def test_selector_returns_correct_number_of_atom_idxs_when_sulfur_atoms_are_selected(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = False
    selector.settings["element"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 10


def test_selector_returns_correct_number_of_atom_idxs_when_sulfur_atoms_are_selected_when_get_idxs_is_called_twice(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = False
    selector.settings["element"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 10
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 10


def test_selector_returns_correct_number_of_atom_idxs_when_waters_are_selected(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = False
    selector.settings["water"] = True
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746


def test_selector_returns_correct_number_of_atom_idxs_when_water_is_turned_on_and_off(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = False
    selector.settings["water"] = True
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746
    selector.settings["water"] = False
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 0


def test_selector_returns_correct_number_of_atom_idxs_when_waters_and_sulfurs_are_selected(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.settings["all"] = False
    selector.settings["water"] = True
    selector.settings["element"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746 + 10


def test_selector_returns_correct_number_of_atom_idxs_when_waters_and_sulfurs_are_selected_with_settings_loaded_as_a_dict(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "element": {"S": True}, "water": True})
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746 + 10


def test_selector_json_dump_0(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "element": {"S": True}})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "element": ["S"]}'


def test_selector_json_dump_1(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "element": {"S": True}, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "element": ["S"]}'


def test_selector_json_dump_2(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true}'


def test_selector_json_dump_3(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings(
        {"all": False, "element": {"S": True, "H": True}, "water": True}
    )
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "element": ["H", "S"]}'


def test_selector_json_dump_4(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings(
        {
            "all": False,
            "element": {"S": True, "H": True},
            "water": True,
            "index": {0: True, 1: True},
        }
    )
    json_dump = selector.settings_to_json()
    assert (
        json_dump
        == '{"all": false, "water": true, "element": ["H", "S"], "index": [0, 1]}'
    )


def test_selector_json_dump_with_second_update(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False})
    selector.update_settings({"element": {"S": True, "O": True}, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "element": ["O", "S"]}'


def test_selector_json_dump_with_third_update(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False})
    selector.update_settings({"element": {"S": True, "O": True}, "water": True})
    selector.update_settings({"element": {"S": False}})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "element": ["O"]}'


def test_selector_json_dump_with_fourth_update(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False})
    selector.update_settings({"element": {"S": True, "O": True}, "water": True})
    selector.update_settings({"element": {"S": False}})
    selector.update_settings({"water": False})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "element": ["O"]}'


def test_selector_returns_correct_number_of_atom_idxs_after_setting_settings_again_with_reset_first(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "element": {"S": True}, "water": True})
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746 + 10

    selector.update_settings(
        {
            "all": False,
            "element": {"S": True},
        },
        reset_first=True,
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 10


def test_selector_json_dump_and_load_0(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "index": {0: True, 1: True}})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "index": [0, 1]}'
    selector.load_from_json(json_dump)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 2


def test_selector_json_dump_and_load_1(protein_trajectory):
    selector = Selector(protein_trajectory)
    selector.update_settings({"all": False, "element": {"S": True}, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "element": ["S"]}'
    selector.load_from_json(json_dump)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746 + 10


def test_selector_returns_correct_number_of_atom_idxs_when_indexes_0_and_1_are_selected(
    protein_trajectory,
):
    selector = Selector(protein_trajectory)
    selector.update_settings(
        {
            "all": False,
            "index": {0: True, 1: True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 2


def test_selector_returns_true_with_correct_setting_check(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert selector.check_valid_setting(
        {
            "all": False,
            "index": {0: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_0(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_setting(
        {
            "alle": False,
            "index": {0: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_1(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_setting(
        {
            "all": False,
            "index": {-1: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_2(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_setting(
        {
            "all": False,
            "index": {0: True, 1: True},
            "element": {"Ss": True},
        }
    )


def test_selector_returns_true_with_correct_json_setting_0(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert selector.check_valid_json_settings(
        '{"all": false, "water": true, "element": {"S": true}}'
    )


def test_selector_returns_true_with_correct_json_setting_1(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert selector.check_valid_json_settings('{"all": false, "index": [0, 1]}')


def test_selector_returns_false_with_incorrect_json_setting_0(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_json_settings(
        '{all: false, "water": true, "element": {"S": true}}'
    )


def test_selector_returns_false_with_incorrect_json_setting_1(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_json_settings('{"all": false, "index": [0, "1"]}')


def test_selector_returns_false_with_incorrect_json_setting_2(protein_trajectory):
    selector = Selector(protein_trajectory)
    assert not selector.check_valid_json_settings('{"all": False, "index": ["0", "1"]}')


@pytest.mark.xfail(reason="see docstring")
def test_selector_with_atom_fullname(protein_trajectory):
    """For the moment, full names of atoms are not implemented
    in the ChemicalSystem."""
    selector = Selector(protein_trajectory)
    selector.update_settings(
        {
            "all": False,
            "fullname": {"...LYS1.N": True, "...VAL2.O": True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 2


@pytest.mark.xfail(reason="see docstring")
def test_selector_with_atom_name(protein_trajectory):
    """At the moment the oxygen in water has the same
    atom name as the oxygen in the protein.
    We will have to decide if this is acceptable.
    """
    selector = Selector(protein_trajectory)
    selector.update_settings(
        {
            "all": False,
            "name": {"N": True, "O": True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 258
