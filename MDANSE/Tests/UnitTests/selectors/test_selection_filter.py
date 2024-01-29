import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.filter_selection import FilterSelection


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb")


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_selection_filter_returns_all_atoms_idxs_when_no_filters_are_set(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.settings["switch"]["elements"] = True
    filter_selection.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 10


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_sulfur_atoms_are_removed_called_twice(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.settings["switch"]["elements"] = True
    filter_selection.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 10
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 10


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_waters_are_removed(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.settings["switch"]["water"] = True
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 28746


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_the_filter_is_turned_on_and_off(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.settings["switch"]["water"] = True
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 28746
    filter_selection.settings["switch"]["water"] = False
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.settings["switch"]["water"] = True
    filter_selection.settings["switch"]["elements"] = True
    filter_selection.settings["args"]["elements"] = {"symbols": ["S"]}
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 28746 - 10


def test_selection_filter_returns_correct_number_of_atoms_idxs_when_waters_and_sulfurs_are_removed_with_settings_loaded_as_a_dict(protein_chemical_system):
    filter_selection = FilterSelection(protein_chemical_system)
    filter_selection.load_settings(
        {
            "switch": {
                "elements": True,
                "water": True
            },
            "args": {
                "elements": {"symbols": ["S"]}
            }
        }
    )
    atm_idxs = filter_selection.apply_filter()
    assert len(atm_idxs) == 30714 - 28746 - 10
