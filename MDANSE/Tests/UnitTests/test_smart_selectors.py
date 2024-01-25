import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.smart_selectors import (
    select_all, select_primary_amine, select_element, select_elements,
    select_hs_on_carbon, select_thiol
)


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Data", "2vb1.pdb")


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_select_all_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_all(protein_chemical_system)
    assert len(selection) == 30714


def test_select_primary_amine_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_primary_amine(protein_chemical_system)
    assert len(selection) == 117


def test_select_element_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_element(protein_chemical_system, "S")
    assert len(selection) == 10

    selection = select_element(protein_chemical_system, "*")
    assert len(selection) == 30714


def test_select_elements_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_elements(protein_chemical_system, ["S", "S"])
    assert len(selection) == 10

    selection = select_elements(protein_chemical_system, ["*", "S"])
    assert len(selection) == 30714


def test_select_hs_on_carbon_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_hs_on_carbon(protein_chemical_system)
    assert len(selection) == 696


def test_select_thiol_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_thiol(protein_chemical_system)
    assert len(selection) == 0
