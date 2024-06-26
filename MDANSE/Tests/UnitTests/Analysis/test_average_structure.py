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
    "short_trajectory_after_changes.mdt",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory

units = ['Angstrom', 'Bohr', 'nm', 'pm']
formats = ['vasp', 'xyz', 'turbomole', 'abinit-in']
inputs = []
for u in units:
    for f in formats:
        inputs.append((u,f))

@pytest.mark.parametrize('output_unit,output_format', inputs)
def test_temperature(trajectory, output_unit, output_format):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_units"] = output_unit
    parameters["fold"] = True
    parameters["output_file"] = (temp_name, output_format)
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    temp = IJob.create("AverageStructure")
    temp.run(parameters, status=True)
    assert path.exists(temp_name)
    assert path.isfile(temp_name)
    os.remove(temp_name)


