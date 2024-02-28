import pytest

from MDANSE.Framework.AtomMapping.atom_mapping import guess_element
from MDANSE.Framework.AtomMapping.atom_mapping import fill_remaining_labels
from MDANSE.Framework.AtomMapping.atom_mapping import get_element_from_mapping
from MDANSE.Framework.AtomMapping.atom_mapping import check_mapping_valid


def test_guess_element_carbon_double_bond_symbol_to_carbon():
    c = guess_element("C=")
    assert c == "C"


def test_guess_element_gold_to_gold():
    au = guess_element("Au")
    assert au == "Au"


def test_guess_element_raise_error_when_unable_to_guess_match():
    with pytest.raises(AttributeError):
        guess_element("aaa")


def test_get_element_from_mapping_with_entry():
    mapping = {"mol1": {"label1": "C"}}
    element = get_element_from_mapping("mol1", "label1", mapping)
    assert element == "C"


def test_get_element_from_mapping_with_no_entry():
    element = get_element_from_mapping("mol1", "C", {})
    assert element == "C"


def test_get_element_from_mapping_with_no_entry_raises_error_with_bad_label():
    with pytest.raises(AttributeError):
        get_element_from_mapping("mol1", "aaa", {})


def test_fill_remaining_labels_fill_mapping_correctly_already_filled():
    labels = [("mol1", "label1"), ("mol1", "label2")]
    mapping = {"mol1": {"label1": "C", "label2": "C"}}
    fill_remaining_labels(labels, mapping)
    assert mapping == {"mol1": {"label1": "C", "label2": "C"}}


def test_fill_remaining_labels_fill_mapping_correctly_missing_mapping():
    labels = [("mol1", "label1"), ("mol1", "C1")]
    mapping = {"mol1": {"label1": "C"}}
    fill_remaining_labels(labels, mapping)
    assert mapping == {"mol1": {"label1": "C", "C1": "C"}}


def test_check_mapping_valid_as_elements_are_correct():
    labels = [("mol1", "label1"), ("mol1", "label2")]
    mapping = {"mol1": {"label1": "C", "label2": "C"}}
    assert check_mapping_valid(labels, mapping)


def test_check_mapping_not_valid_as_elements_not_correct():
    labels = [("mol1", "label1"), ("mol1", "label2")]
    mapping = {"mol1": {"label1": "C", "label2": "aaa"}}
    assert not check_mapping_valid(labels, mapping)


def test_check_mapping_not_valid_due_to_missing_mappings():
    labels = [("mol1", "label1"), ("mol1", "label2")]
    mapping = {"mol1": {"label1": "C"}}
    assert not check_mapping_valid(labels, mapping)
