import pytest
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "co2gas_md3.mdt"


@pytest.fixture(scope="module")
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory


def test_unit_cell(trajectory: Trajectory):
    configuration = trajectory.configuration()
    unit_cell = configuration.unit_cell
    print(unit_cell.abc_and_angles)


def test_molecule_finder(trajectory: Trajectory):
    configuration = trajectory.configuration()
    coordinates = configuration._variables["coordinates"]
    print(coordinates.shape)
