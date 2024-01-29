import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.selector import Selector


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_Selector_returns_all_atoms_idxs(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["switch"]["elements"] = -1
    selector.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed_called_twice(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["switch"]["elements"] = -1
    selector.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 10
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["switch"]["water"] = -1
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746


def test_selector_returns_correct_number_of_atoms_idxs_when_the_filter_is_turned_on_and_off(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["switch"]["water"] = -1
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746
    selector.settings["switch"]["water"] = 0
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.settings["switch"]["water"] = -1
    selector.settings["switch"]["elements"] = -1
    selector.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed_with_settings_loaded_as_a_dict(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "switch": {"elements": -1, "water": -1},
            "args": {"elements": {"symbols": ["S"]}},
        }
    )
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_json_dump_and_load(protein_chemical_system):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "switch": {"elements": -1, "water": -1},
            "args": {"elements": {"symbols": ["S"]}},
        }
    )
    json_dump = selector.settings_to_json()
    selector.settings_from_json(json_dump)
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selector_returns_correct_number_of_atoms_idxs_after_setting_settings_again_with_reset_first(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "switch": {"elements": -1, "water": -1},
            "args": {"elements": {"symbols": ["S"]}},
        }
    )
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 28746 - 10

    selector.update_settings(
        {
            "switch": {
                "elements": -1,
            },
            "args": {"elements": {"symbols": ["S"]}},
        },
        reset_first=True,
    )
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 10


def test_selector_returns_correct_number_of_atoms_idxs_when_sulfurs_and_then_all_atoms_are_removed(
    protein_chemical_system,
):
    selector = Selector(protein_chemical_system)
    selector.update_settings(
        {
            "switch": {"elements": -1},
            "args": {"elements": {"symbols": ["S"]}},
        }
    )
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 30714 - 10

    selector.update_settings(
        {
            "switch": {"elements": -1},
            "args": {"elements": {"symbols": ["S", "*"]}},
        }
    )
    atm_idxs = selector.get_selection()
    assert len(atm_idxs) == 0
