from contextlib import nullcontext as success

import pytest
from MDANSE.Chemistry.Databases import AtomsDatabaseError
from MDANSE.Framework.AtomMapping.atom_mapping import (
    AtomLabel, check_mapping_valid, fill_remaining_labels,
    get_element_from_mapping, guess_element)
from MDANSE.Framework.Units import measure


@pytest.mark.parametrize("key, mass, expected", [
    ("1H", None, success("H")),
    ("h", None, success("H")),
    ("C=", None, success("C")),
    ("Au", None, success("Au")),
    ("NA", None, success("Na")),
    ("CL", None, success("Cl")),

    ("C", 12, success("C12")),
    ("C", 13, success("C13")),
    ("C", 12.01, success("C")),
    ("H", 2, success("H2")),
    ("NA", 22.98977, success("Na")),
    ("SOD", 22.98977, success("Na")),

    ("aaa", None, pytest.raises(AttributeError, match="Unable to guess")),
    ("C", -1, pytest.raises(AtomsDatabaseError, match="must be a numeric type")),
    (1, None, pytest.raises(AttributeError, match=" no attribute 'upper'")),
    ("H", "mass", pytest.raises(TypeError, match="unsupported operand")),
    ("H", measure(1., "kg"), pytest.raises(AttributeError,
                                           match="no attribute '_dimension'")),
])
def test_guess_element(key, mass, expected):
    with expected as val:
        assert guess_element(key, mass) == val

@pytest.mark.parametrize("mapping, params, expected", [
    ({"": {"label1": "C"}}, {"label": "label1"}, success("C")),

    ({"molecule=mol1": {"label1": "C"}},
     {"label": "label1", "molecule": "mol1"}, success("C")),

    ({"grp1=1;grp2=1": {"label1": "C"}},
     {"label": "label1", "grp1": "1", "grp2": "1"}, success("C")),

    ({}, {"label": "C"}, success("C")),

    ({}, {"label": "aaa", "molecule": "mol1"}, pytest.raises(AttributeError)),
], ids=["unlabelled", "molecule", "group", "nomapping", "fail"])
def test_get_element_from_mapping(mapping, params, expected):
    with expected as val:
        assert get_element_from_mapping(mapping, **params) == val

@pytest.mark.parametrize("labels, mapping, expected", [
    ([AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")],
     {"molecule=mol1": {"label1": "C", "label2": "C"}},
     success({"molecule=mol1": {"label1": "C", "label2": "C"}})),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("label1", molecule="mol1")],
     {"molecule=mol1": {"label1": "C"}},
     success({"molecule=mol1": {"label1": "C"}}),
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
     {"molecule=mol1": {"label1": "C"}},
     success({"molecule=mol1": {"label1": "C", "C1": "C"}}),
     )
])
def test_fill_remaining_labels(labels, mapping, expected):
    fill_remaining_labels(mapping, labels)
    with expected as val:
        assert mapping == val

@pytest.mark.parametrize("labels, mapping, expected", [
    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
     {"molecule=mol1": {"label1": "C", "C1": "C"}},
     True,
    ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
     {"molecule=mol1": {"C1": "C", "label1": "C"}},
     True,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol2")],
     {"molecule=mol1": {"label1": "C"}, "molecule=mol2": {"C1": "C"}},
     True,
     ),

    ([AtomLabel("label1", type="1*"), AtomLabel("C1", type="2*")],
     {"type=1*": {"label1": "C"}, "type=2*": {"C1": "C"}},
     True,
     ),

    ([AtomLabel("label1", mass="12"), AtomLabel("C1", mass="13")],
     {"mass=12": {"label1": "C"}, "mass=13": {"C1": "C"}},
     True,
     ),

    ([AtomLabel("label=1", molecule="mol=1"), AtomLabel("C=1", molecule="mol=2")],
     {"molecule=mol1": {"label1": "C"}, "molecule=mol2": {"C1": "C"}},
     True,
     ),

    ([AtomLabel("label=1"), AtomLabel("C=1")],
     {"": {"label1": "C", "C1": "C"}},
     True,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")],
     {"molecule=mol1": {"label1": "C", "label2": "aaa"}},
     False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("label2", molecule="mol1")],
    {"molecule=mol1": {"label1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol2")],
    {"molecule=mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule=mol1": {"label1": "C", "label2": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule=mol1": {"label1": "C", "C1": "C", "label2": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule==mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule===mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule=mol1;": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {";molecule=mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule;=mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"mole;cule=mol1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol1")],
    {"molecule=mo;l1": {"label1": "C", "C1": "C"}},
    False,
     ),

    ([AtomLabel("label1", molecule="mol1"), AtomLabel("C1", molecule="mol2")],
    {"molecule=mol1": {"label1": "C"}, "molec;ule=mol2": {"C1": "C"}},
    False,
     ),
])
def test_check_mapping_valid(mapping, labels, expected):
    assert check_mapping_valid(mapping, labels) is expected
