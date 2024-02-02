import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.AtomSelector.atom_selectors import (
    select_element,
    select_hs_on_heteroatom,
    select_hs_on_element,
)


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_select_element_returns_true_as_match_exist(
    protein_chemical_system,
):
    exists = select_element(protein_chemical_system, "S", check_exists=True)
    assert exists


def test_select_element_returns_false_as_match_does_not_exist(
    protein_chemical_system,
):
    exists = select_element(protein_chemical_system, "Si", check_exists=True)
    assert not exists


def test_select_element_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_element(protein_chemical_system, "S")
    assert len(selection) == 10


def test_select_hs_on_carbon_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_element(protein_chemical_system, "C")
    assert len(selection) == 696


def test_select_hs_on_nitrogen_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_element(protein_chemical_system, "N")
    assert len(selection) == 243


def test_select_hs_on_oxygen_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_element(protein_chemical_system, "O")
    assert len(selection) == 19184


def test_select_hs_on_sulfur_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_element(protein_chemical_system, "S")
    assert len(selection) == 0


def test_select_hs_on_silicon_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_element(protein_chemical_system, "Si")
    assert len(selection) == 0


def test_select_hs_on_heteroatom_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_heteroatom(protein_chemical_system)
    assert len(selection) == 19427
