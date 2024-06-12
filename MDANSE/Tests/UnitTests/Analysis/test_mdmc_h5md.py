import sys
import tempfile
import os
from os import path
import pytest
from icecream import ic
import numpy as np
import h5py
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "test_file.h5",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


@pytest.mark.parametrize("interp_order", [1, 3])
def test_temperature_nonzero(trajectory, interp_order):
    print(f"Trajectory length: {len(trajectory.trajectory)}")
    print(f"Positions array shape: {trajectory.trajectory.variable('position').shape}")
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["interpolation_order"] = interp_order
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    temp = IJob.create("Temperature")
    temp.run(parameters, status=True)
    with h5py.File(temp_name + ".mda") as results:
        print(results.keys())
        temperature = np.array(results["/temperature"])
    os.remove(temp_name + ".mda")
    assert np.all(temperature > 0.0)

