import sys
import tempfile
import os
from os import path
import pytest

import numpy as np
import h5py
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


@pytest.mark.parametrize("interp_order", [1, 2, 3])
def test_temperature(trajectory, interp_order):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["interpolation_order"] = interp_order
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    temp = IJob.create("Temperature")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")


@pytest.mark.parametrize("interp_order", [1, 2, 3])
def test_temperature_nonzero(trajectory, interp_order):
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


@pytest.mark.parametrize("output_format", ["MDAFormat", "TextFormat"])
def test_density(trajectory, output_format):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, (output_format,))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    den = IJob.create("Density")
    den.run(parameters, status=True)
    if output_format == "MDAFormat":
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
        os.remove(temp_name + ".mda")
    elif output_format == "TextFormat":
        assert path.exists(temp_name + "_text.tar")
        assert path.isfile(temp_name + "_text.tar")
        os.remove(temp_name + "_text.tar")
