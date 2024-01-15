import os
import numpy as np
from rdkit.Chem.rdmolfiles import MolFromPDBFile
from rdkit.Chem.rdchem import Mol, GetPeriodicTable
from rdkit.Chem.rdmolops import SanitizeMol
from rdkit.Chem.rdmolops import GetMolFrags
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


fname = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "CO2GAS-dump-1.pdb")


@pytest.fixture()
def chem_from_pdb():
    reader = PDBReader(fname)
    chem = reader.build_chemical_system()
    yield chem


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
    all_lengths = np.array([mol.GetNumAtoms() for mol in gas_bits])
    assert len(gas_bits) == 20
    assert np.all(all_lengths == 3)


def test_periodic():
    ptable = GetPeriodicTable()
    for element in ["H", "C", "O", "Fe", "Cu", "Ne", "Cl"]:
        cov = ptable.GetRcovalent(element)
        vdw = ptable.GetRvdw(element)
        print(element, cov, vdw)
    # assert False  # this was just to trigger the printout
