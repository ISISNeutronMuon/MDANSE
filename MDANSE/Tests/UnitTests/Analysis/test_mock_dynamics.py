import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np

from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)

file_wd = os.path.dirname(os.path.realpath(__file__))

mock_json = os.path.join(file_wd, "..", "Data", "mock.json")

@pytest.fixture(scope="module")
def mock_trajectory():
    """Returns a trajectory containing muiltiple atoms,
    in a supercell, which move periodically.
    """
    traj = MockTrajectory.from_json(mock_json)
    return traj


@pytest.mark.parametrize(
    "interp_order, normalise",
    [
        (1, True),
        (2, True),
        (3, True),
        (1, False),
        (2, False),
        (3, False),
    ],
)
def test_vacf(mock_trajectory, interp_order, normalise):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["interpolation_order"] = interp_order
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("monoprocessor",)
    parameters["normalize"] = normalise
    parameters["trajectory"] = mock_trajectory
    vacf = IJob.create("VelocityAutoCorrelationFunction")
    vacf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
