import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "co2gas_md3.mdt"
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_unit_cell(trajectory: HDFTrajectoryInputData):
    configuration = trajectory._data.configuration()
    unit_cell = configuration.unit_cell
    print(unit_cell.abc_and_angles)


def test_molecule_finder(trajectory: HDFTrajectoryInputData):
    configuration = trajectory._data.configuration()
    coordinates = configuration._variables["coordinates"]
    print(coordinates.shape)
