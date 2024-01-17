import os
import pytest
import numpy as np
from rdkit.Chem.rdmolops import SanitizeMol
from rdkit.Chem.rdmolops import GetMolFrags
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Chemistry.Structrures import Topology


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "co2gas_md3.h5")


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_unit_cell(trajectory: HDFTrajectoryInputData):
    chem_system = trajectory.chemical_system
    configuration = chem_system.configuration
    unit_cell = configuration.unit_cell
    print(unit_cell.abc_and_angles)


def test_molecule_finder(trajectory: HDFTrajectoryInputData):
    chem_system = trajectory.chemical_system
    configuration = chem_system.configuration
    coordinates = configuration._variables["coordinates"]
    print(coordinates.shape)


@pytest.mark.xfail(reason="see docstring")
def test_molecule_assignment(trajectory: HDFTrajectoryInputData):
    """As of today (17 Oct 2023) this test does not pass.
    Topology class writes out the atom coordinates to a PDB file buffer,
    and RDKit scans it for molecules.
    Apparently RDKit does not apply the periodic boundary conditions,
    and the molecules that were on the edge of the simulation box
    end up in several pieces.
    At the moment we use the Connectivity class instead.
    """
    chem_system = trajectory.chemical_system
    configuration = chem_system.configuration
    topology = Topology(trajectory, chem_system)
    mol = topology.scan_trajectory_frame(0)
    SanitizeMol(mol)
    gas_bits = GetMolFrags(mol, asMols=True)
    all_lengths = np.array([mol.GetNumAtoms() for mol in gas_bits])
    # assert len(gas_bits) == 20
    assert np.all(all_lengths == 3)
