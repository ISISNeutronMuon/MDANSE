import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.Selectors.all_selector import select_all


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb")


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_select_all_returns_correct_number_of_atoms_matches(protein_chemical_system):
    selection = select_all(protein_chemical_system)
    assert len(selection) == 30714
