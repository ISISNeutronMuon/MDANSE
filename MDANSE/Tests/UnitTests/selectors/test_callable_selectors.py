import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.callable_selectors import (
    select_with_fullname,
    select_with_name
)


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb")


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_select_with_fullname_returns_correct_number_of_atoms(protein_chemical_system):
    selection = select_with_fullname(
        protein_chemical_system, ["...LYS1.N", "...VAL2.O"])
    assert len(selection) == 2


def test_select_with_name_returns_correct_number_of_atoms(protein_chemical_system):
    selection = select_with_name(protein_chemical_system, ["N", "O"])
    assert len(selection) == 258
