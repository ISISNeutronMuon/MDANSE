import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.AtomSelector.molecule_selectors import select_water


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_select_water_returns_true_as_match_exists(
    protein_chemical_system,
):
    exists = select_water(protein_chemical_system, check_exists=True)
    assert exists


def test_select_water_returns_correct_number_of_atom_matches(
    protein_chemical_system,
):
    selection = select_water(protein_chemical_system)
    assert len(selection) == 28746
