import sys
import tempfile
import os
from os import path
import pytest

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "Data",
    "short_trajectory_after_changes.mdt",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_temperature(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["interpolation_order"] = 3
    parameters["output_files"] = (temp_name, ("TextFormat",), False)
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    temp = IJob.create("Temperature")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
