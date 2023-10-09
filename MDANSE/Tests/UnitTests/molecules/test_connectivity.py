import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np
from rdkit.Chem import Mol
from rdkit.Chem.rdmolops import SanitizeMol
from rdkit.Chem.rdmolops import GetMolFrags

from MDANSE import REGISTRY
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Chemistry.Structrures import Topology

short_traj = 'co2gas_md3.h5'

@pytest.fixture(scope="module")
def trajectory() -> HDFTrajectoryInputData:
    trajectory = REGISTRY["input_data"]["hdf_trajectory"](short_traj)
    yield trajectory

def test_create_connectivity(trajectory: HDFTrajectoryInputData):
    conn = Connectivity(trajectory=trajectory)
    print(conn._unique_elements)
    assert len(conn._unique_elements) == 2

def test_find_bonds(trajectory: HDFTrajectoryInputData):
    conn = Connectivity(trajectory=trajectory)
    conn.find_bonds()
    assert len(conn._unique_bonds) == 40

def test_find_molecules(trajectory: HDFTrajectoryInputData):
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    assert len(conn._molecules) == 20

def test_rebuild_molecules(trajectory: HDFTrajectoryInputData):
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    atoms_before = int(trajectory.chemical_system.number_of_atoms)
    chemical_system = trajectory.chemical_system
    print(conn._molecules)
    chemical_system.rebuild(conn._molecules)
    atoms_after = int(trajectory.chemical_system.number_of_atoms)
    assert atoms_before == atoms_after
