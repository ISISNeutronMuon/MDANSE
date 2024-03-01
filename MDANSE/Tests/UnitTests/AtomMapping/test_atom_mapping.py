import pytest

from MDANSE.Framework.AtomMapping.atom_mapping import guess_element
from MDANSE.Framework.AtomMapping.atom_mapping import fill_remaining_labels
from MDANSE.Framework.AtomMapping.atom_mapping import get_element_from_mapping
from MDANSE.Framework.AtomMapping.atom_mapping import check_mapping_valid
from MDANSE.Framework.AtomMapping.atom_mapping import AtomLabel


def test_guess_element_carbon_double_bond_symbol_to_carbon():
    c = guess_element("C=")
    assert c == "C"


def test_guess_element_gold_to_gold():
    au = guess_element("Au")
    assert au == "Au"


def test_guess_element_raise_error_when_unable_to_guess_match():
    with pytest.raises(AttributeError):
        guess_element("aaa")


def test_guess_element_carbon_symbol_to_carbon_12():
    c = guess_element("C", mass=12)
    assert c == "C12"


def test_guess_element_carbon_symbol_to_carbon_13():
    c = guess_element("C", mass=13)
    assert c == "C13"


def test_guess_element_carbon_symbol_to_carbon():
    c = guess_element("C", mass=12.01)
    assert c == "C"


def test_get_element_from_mapping_with_entry_but_no_kwargs():
    mapping = {"": {"label1": "C"}}
    element = get_element_from_mapping(mapping, "label1")
    assert element == "C"


def test_get_element_from_mapping_with_entry():
    mapping = {"molecule=mol1": {"label1": "C"}}
    element = get_element_from_mapping(mapping, "label1", molecule="mol1")
    assert element == "C"


def test_get_element_from_mapping_with_entry_two_group_labels():
    mapping = {"grp1=1;grp2=1": {"label1": "C"}}
    element = get_element_from_mapping(mapping, "label1", grp1="1", grp2="1")
    assert element == "C"


def test_get_element_from_mapping_with_no_entry():
    element = get_element_from_mapping({}, "C", molecule="mol1")
    assert element == "C"


def test_get_element_from_mapping_with_no_entry_raises_error_with_bad_label():
    with pytest.raises(AttributeError):
        get_element_from_mapping({}, "aaa", molecule="mol1")


def test_fill_remaining_labels_fill_mapping_correctly_already_filled_1():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C", "label2": "C"}}
    fill_remaining_labels(mapping, labels)
    assert mapping == {"molecule=mol1": {"label1": "C", "label2": "C"}}


def test_fill_remaining_labels_fill_mapping_correctly_already_filled_2():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("label1", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C"}}
    fill_remaining_labels(mapping, labels)
    assert mapping == {"molecule=mol1": {"label1": "C"}}


def test_fill_remaining_labels_fill_mapping_correctly_missing_mapping():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C"}}
    fill_remaining_labels(mapping, labels)
    assert mapping == {"molecule=mol1": {"label1": "C", "C1": "C"}}


def test_check_mapping_valid_as_elements_are_correct():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C", "C1": "C"}}
    assert check_mapping_valid(mapping, labels)


def test_check_mapping_not_valid_as_elements_not_correct():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C", "label2": "aaa"}}
    assert not check_mapping_valid(mapping, labels)


def test_check_mapping_not_valid_due_to_missing_mappings():
    labels = [AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")]
    mapping = {"molecule=mol1": {"label1": "C"}}
    assert not check_mapping_valid(mapping, labels)
