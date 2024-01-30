import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.AtomSelector.filter_selection import FilterSelection


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_filter_returns_all_atoms_idxs(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714


def test_filter_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.settings["elements"] = {"S": True}
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_filter_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed_when_get_idxs_is_called_twice(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.settings["elements"] = {"S": True}
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 10
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_filter_returns_correct_number_of_atoms_idxs_when_waters_are_removed(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.settings["water"] = True
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746


def test_filter_returns_correct_number_of_atoms_idxs_when_water_filter_is_turned_on_and_off(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.settings["water"] = True
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746
    filter.settings["water"] = False
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714


def test_filter_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.settings["water"] = True
    filter.settings["elements"] = {"S": True}
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_filter_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed_with_settings_loaded_as_a_dict(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_filter_json_dump_0(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"elements": {"S": true}}'


def test_filter_json_dump_1(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"S": true}}'


def test_filter_json_dump_2(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"water": True})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true}'


def test_filter_json_dump_3(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True, "H": True}, "water": True})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"S": true, "H": true}}'


def test_filter_json_dump_4(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True, "H": True}, "water": True, "index": {0: True, 1: True}})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"S": true, "H": true}, "index": {"0": true, "1": true}}'


def test_filter_json_dump_with_second_update(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    filter.update_settings({"elements": {"O": True}})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"S": true, "O": true}}'


def test_filter_json_dump_with_third_update(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    filter.update_settings({"elements": {"O": True}})
    filter.update_settings({"elements": {"S": False}})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"O": true}}'


def test_filter_json_dump_with_fourth_update(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    filter.update_settings({"elements": {"O": True}})
    filter.update_settings({"elements": {"S": False}})
    filter.update_settings({"water": False})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"elements": {"O": true}}'


def test_filter_json_dump_and_load_0(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"index": {0: True, "1": True}})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"index": {"0": true, "1": true}}'
    filter.update_from_json(json_dump)
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 2


def test_filter_json_dump_and_load_1(protein_chemical_system):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    json_dump = filter.settings_to_json()
    assert json_dump == '{"water": true, "elements": {"S": true}}'
    filter.update_from_json(json_dump)
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_filter_returns_correct_number_of_atoms_idxs_after_setting_settings_again_with_reset_first(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings({"elements": {"S": True}, "water": True})
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 28746 - 10

    filter.update_settings(
        {
            "elements": {"S": True},
        },
        reset_first=True,
    )
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 10


def test_filter_returns_correct_number_of_atoms_idxs_when_sulfurs_and_then_all_atoms_are_removed(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings(
        {
            "elements": {"S": True},
        }
    )
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 10

    filter.update_settings(
        {
            "elements": {"*": True},
        }
    )
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 0


def test_filter_returns_correct_number_of_atoms_idxs_when_indexes_0_and_1_are_removed(
    protein_chemical_system,
):
    filter = FilterSelection(protein_chemical_system)
    filter.update_settings(
        {
            "index": {0: True, 1: True},
        }
    )
    atm_idxs = filter.get_idxs()
    assert len(atm_idxs) == 30714 - 2
