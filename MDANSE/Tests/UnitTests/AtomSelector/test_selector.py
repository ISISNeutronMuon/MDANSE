import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.AtomSelector.selector import Selector


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_selector_returns_all_atoms_idxs(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714


def test_selector_returns_all_atoms_idxs_with_all_and_sulfurs_selected(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["all"] = True
    selector.settings["elements"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_selected(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["all"] = False
    selector.settings["elements"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 10


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["reverse"] = True
    selector.settings["all"] = False
    selector.settings["elements"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed_when_get_idxs_is_called_twice(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["reverse"] = True
    selector.settings["all"] = False
    selector.settings["elements"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 10
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_are_selected(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["all"] = False
    selector.settings["water"] = True
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 28746


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["reverse"] = True
    selector.settings["all"] = False
    selector.settings["water"] = True
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746


def test_selector_returns_correct_number_of_atoms_idxs_when_water_is_turned_on_and_off(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["reverse"] = True
    selector.settings["all"] = False
    selector.settings["water"] = True
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746
    selector.settings["water"] = False
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["reverse"] = True
    selector.settings["all"] = False
    selector.settings["water"] = True
    selector.settings["elements"] = {"S": True}
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed_with_settings_loaded_as_a_dict(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {"reverse": True, "all": False, "elements": {"S": True}, "water": True}
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_json_dump_0(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False, "elements": {"S": True}})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "elements": {"S": true}}'


def test_selector_json_dump_1(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False, "elements": {"S": True}, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "elements": {"S": true}}'


def test_selector_json_dump_2(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False, "water": True})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true}'


def test_selector_json_dump_3(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {"all": False, "elements": {"S": True, "H": True}, "water": True}
    )
    json_dump = selector.settings_to_json()
    assert (
        json_dump == '{"all": false, "water": true, "elements": {"S": true, "H": true}}'
    )


def test_selector_json_dump_4(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "all": False,
            "elements": {"S": True, "H": True},
            "water": True,
            "index": {0: True, 1: True},
        }
    )
    json_dump = selector.settings_to_json()
    assert (
        json_dump
        == '{"all": false, "water": true, "elements": {"S": true, "H": true}, "index": {"0": true, "1": true}}'
    )


def test_selector_json_dump_with_second_update(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False})
    selector.update_settings({"elements": {"S": True, "O": True}, "water": True})
    json_dump = selector.settings_to_json()
    assert (
        json_dump == '{"all": false, "water": true, "elements": {"S": true, "O": true}}'
    )


def test_selector_json_dump_with_third_update(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False})
    selector.update_settings({"elements": {"S": True, "O": True}, "water": True})
    selector.update_settings({"elements": {"S": False}})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "water": true, "elements": {"O": true}}'


def test_selector_json_dump_with_fourth_update(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings({"all": False})
    selector.update_settings({"elements": {"S": True, "O": True}, "water": True})
    selector.update_settings({"elements": {"S": False}})
    selector.update_settings({"water": False})
    json_dump = selector.settings_to_json()
    assert json_dump == '{"all": false, "elements": {"O": true}}'


def test_selector_returns_correct_number_of_atoms_idxs_after_setting_settings_again_with_reset_first(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {"reverse": True, "all": False, "elements": {"S": True}, "water": True}
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10

    selector.update_settings(
        {
            "reverse": True,
            "all": False,
            "elements": {"S": True},
        },
        reset_first=True,
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_selector_json_dump_and_load_0(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {"reverse": True, "all": False, "index": {0: True, "1": True}}
    )
    json_dump = selector.settings_to_json()
    assert (
        json_dump == '{"reverse": true, "all": false, "index": {"0": true, "1": true}}'
    )
    selector.update_from_json(json_dump, reset_first=True)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 2


def test_selector_json_dump_and_load_1(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {"reverse": True, "all": False, "elements": {"S": True}, "water": True}
    )
    json_dump = selector.settings_to_json()
    assert (
        json_dump
        == '{"reverse": true, "all": false, "water": true, "elements": {"S": true}}'
    )
    selector.update_from_json(json_dump, reset_first=True)
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfurs_and_then_all_atoms_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "reverse": True,
            "all": False,
            "elements": {"S": True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 10

    selector.update_settings(
        {
            "elements": {"*": True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 0


def test_selector_returns_correct_number_of_atoms_idxs_when_indexes_0_and_1_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "reverse": True,
            "all": False,
            "index": {0: True, 1: True},
        }
    )
    atm_idxs = selector.get_idxs()
    assert len(atm_idxs) == 30714 - 2


def test_selector_returns_true_with_correct_setting_check(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert selector.check_valid_setting(
        {
            "reverse": True,
            "all": False,
            "index": {0: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_0(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_setting(
        {
            "reversee": True,
            "all": False,
            "index": {0: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_1(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_setting(
        {
            "reverse": True,
            "all": False,
            "index": {-1: True, 1: True},
        }
    )


def test_selector_returns_false_with_incorrect_setting_check_2(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_setting(
        {
            "reverse": True,
            "all": False,
            "index": {0: True, 1: True},
            "elements": {"Ss": True},
        }
    )


def test_selector_returns_true_with_correct_json_setting_0(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert selector.check_valid_json_settings(
        '{"reverse": true, "all": false, "water": true, "elements": {"S": true}}'
    )


def test_selector_returns_true_with_correct_json_setting_1(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert selector.check_valid_json_settings(
        '{"reverse": true, "all": false, "index": {"0": true, "1": true}}'
    )


def test_selector_returns_false_with_incorrect_json_setting_0(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_json_settings(
        '{reverse: true, "all": false, "water": true, "elements": {"S": true}}'
    )


def test_selector_returns_false_with_incorrect_json_setting_1(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_json_settings(
        '{"reverse": true, "all": false, "index": {0: true, "1": true}}'
    )


def test_selector_returns_false_with_incorrect_json_setting_2(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    assert not selector.check_valid_json_settings(
        '{"reverse": True, "all": false, "index": {"0": true, "1": true}}'
    )
