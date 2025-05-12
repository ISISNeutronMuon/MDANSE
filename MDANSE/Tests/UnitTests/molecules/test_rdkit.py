import numpy as np
import pytest
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.IO.MinimalPDBReader import MinimalPDBReader as PDBReader
from rdkit.Chem.rdchem import GetPeriodicTable, Mol
from rdkit.Chem.rdmolfiles import MolFromPDBFile
from rdkit.Chem.rdmolops import GetMolFrags, SanitizeMol
from test_helpers.paths import DATA_DIR

fname = DATA_DIR / "CO2GAS-dump-1.pdb"


@pytest.fixture()
def chem_from_pdb():
    reader = PDBReader(fname)
    yield reader._chemical_system


@pytest.fixture()
def mol_from_rdkit():
    mol = MolFromPDBFile(fname)
    yield mol


def test_loader(chem_from_pdb: ChemicalSystem):
    assert chem_from_pdb.number_of_atoms == 60


def test_rdkit(mol_from_rdkit: Mol):
    SanitizeMol(mol_from_rdkit)
    print(
        [
            (bond.GetBeginAtom().GetIdx(), bond.GetEndAtom().GetIdx())
            for bond in mol_from_rdkit.GetBonds()
        ]
    )
    assert mol_from_rdkit.GetNumAtoms() == 60


def test_splitting(mol_from_rdkit: Mol):
    gas_bits = GetMolFrags(mol_from_rdkit, asMols=True)
    assert len(gas_bits) == 20
    assert all(mol.GetNumAtoms() == 3 for mol in gas_bits)


def test_periodic():
    ptable = GetPeriodicTable()
    for element in ["H", "C", "O", "Fe", "Cu", "Ne", "Cl"]:
        cov = ptable.GetRcovalent(element)
        vdw = ptable.GetRvdw(element)
        print(element, cov, vdw)
