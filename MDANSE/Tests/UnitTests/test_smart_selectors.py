import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.smart_selectors import (
    select_all,
    select_primary_amine,
    select_element,
    select_elements,
    select_hs_on_element,
    select_hs_on_heteroatom,
    select_hydroxy,
    select_methly,
    select_phosphate,
    select_sulphate,
    select_thiol,
)


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Data", "2vb1.pdb")
pbd_1gip = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Data", "1gip.pdb")


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


@pytest.fixture(scope="module")
def nucleic_acid_chemical_system():
    reader = PDBReader(pbd_1gip)
    nucleic_acid_chemical_system = reader.build_chemical_system()
    return nucleic_acid_chemical_system


def test_select_all_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_all(protein_chemical_system)
    assert len(selection) == 30714


def test_select_primary_amine_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_primary_amine(protein_chemical_system)
    assert len(selection) == 117


def test_select_element_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_element(protein_chemical_system, "S")
    assert len(selection) == 10

    selection = select_element(protein_chemical_system, "*")
    assert len(selection) == 30714


def test_select_elements_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_elements(protein_chemical_system, ["S", "S"])
    assert len(selection) == 10

    selection = select_elements(protein_chemical_system, ["*", "S"])
    assert len(selection) == 30714


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


def test_select_hs_on_heteroatom_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hs_on_heteroatom(protein_chemical_system)
    assert len(selection) == 19427


def test_select_hydroxy_returns_correct_number_of_atoms_matches(
    protein_chemical_system,
):
    selection = select_hydroxy(protein_chemical_system)
    assert len(selection) == 28786


def test_select_methyl_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_methly(protein_chemical_system)
    assert len(selection) == 244


def test_select_phosphate_returns_correct_number_of_atoms_matches(
    nucleic_acid_chemical_system,
):
    selection = select_phosphate(nucleic_acid_chemical_system)
    assert len(selection) == 110


def test_select_sulphate_returns_correct_number_of_atoms_matches(
    nucleic_acid_chemical_system,
):
    selection = select_sulphate(nucleic_acid_chemical_system)
    assert len(selection) == 0


def test_select_thiol_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_thiol(protein_chemical_system)
    assert len(selection) == 0
