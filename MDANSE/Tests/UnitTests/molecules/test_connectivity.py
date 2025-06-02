import pytest
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "co2gas_md3.mdt"


@pytest.fixture
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory

@pytest.fixture
def connectivity(trajectory):
    conn = Connectivity(trajectory=trajectory)
    conn.find_bonds()
    return conn

def test_create_connectivity(trajectory):
    conn = Connectivity(trajectory=trajectory)
    assert len(conn._unique_elements) == 2


def test_find_molecules(trajectory, connectivity):
    assert len(connectivity._unique_bonds) == 40

    connectivity.add_bond_information(trajectory.chemical_system)

    csys = trajectory.chemical_system
    molecules_found = sum(csys.number_of_molecules(name)
                          for name in csys.unique_molecules())
    assert molecules_found == 20


def test_identify_molecules(trajectory, connectivity):
    connectivity.find_bonds()
    chemical_system = trajectory.chemical_system
    connectivity.add_bond_information(chemical_system)

    molstrings = []
    assert all(len(mollist) == 20
               for mollist in chemical_system._clusters.values())
    assert all(ms == molstrings[0] for ms in molstrings[1:])
    assert len(chemical_system.unique_molecules()) == 1
