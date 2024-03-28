import os
import pytest
import numpy as np
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.Chemistry.Structrures import MoleculeTester


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "co2gas_md3.mdt"
)


@pytest.fixture
def trajectory() -> HDFTrajectoryInputData:
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory.trajectory


def test_create_connectivity(trajectory: Trajectory):
    conn = Connectivity(trajectory=trajectory)
    print(conn._unique_elements)
    assert len(conn._unique_elements) == 2


def test_find_bonds(trajectory: Trajectory):
    conn = Connectivity(trajectory=trajectory)
    conn.find_bonds()
    assert len(conn._unique_bonds) == 40


def test_find_molecules(trajectory: Trajectory):
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    assert len(conn._molecules) == 20


def test_rebuild_molecules(trajectory: Trajectory):
    print(trajectory.chemical_system.atom_list)
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    atoms_before = int(trajectory.chemical_system.number_of_atoms)
    chemical_system = trajectory.chemical_system
    print(conn._molecules)
    chemical_system.rebuild(conn._molecules)
    atoms_after = int(trajectory.chemical_system.number_of_atoms)
    assert atoms_before == atoms_after


def test_unwrap_molecules(trajectory: Trajectory):
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    chemical_system = trajectory.chemical_system
    original_coords = chemical_system.configuration.coordinates
    # print([atom.name for atom in chemical_system.atoms])
    chemical_system.rebuild(conn._molecules)
    configuration = chemical_system.configuration
    contiguous_config = configuration.contiguous_configuration()
    # print([atom.name for atom in chemical_system.atoms])
    # print(cc.coordinates)
    assert not np.allclose(original_coords, contiguous_config.coordinates)


def test_identify_molecules(trajectory: Trajectory):
    conn = Connectivity(trajectory=trajectory)
    conn.find_molecules()
    chemical_system = trajectory.chemical_system
    chemical_system.rebuild(conn._molecules)
    configuration = chemical_system.configuration
    coords = configuration.contiguous_configuration().coordinates
    molstrings = []
    for entity in chemical_system.chemical_entities:
        moltester = MoleculeTester(entity, coords)
        inchistring = moltester.identify_molecule()
        molstrings.append(inchistring)
        if entity.number_of_atoms > 1:
            entity.name = inchistring
    assert len(molstrings) == 20
    result = True
    for ms in molstrings[1:]:
        result = result and ms == molstrings[0]
    assert result
    print(chemical_system.unique_molecules())
    assert len(chemical_system.unique_molecules()) == 1
