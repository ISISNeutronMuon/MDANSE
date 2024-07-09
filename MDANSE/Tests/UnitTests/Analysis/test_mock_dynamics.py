import sys
import tempfile
import os
from os import path

import pytest

from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)

short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)

file_wd = os.path.dirname(os.path.realpath(__file__))

mock_json = os.path.join(file_wd, "..", "Data", "mock.json")


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
def test_vacf(interp_order, normalise):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1, 5)
    parameters["interpolation_order"] = interp_order
    parameters["output_files"] = (temp_name, ("MDAFormat",), True)
    parameters["running_mode"] = ("single-core",)
    parameters["normalize"] = normalise
    parameters["trajectory"] = mock_json
    vacf = IJob.create("VelocityAutoCorrelationFunction", trajectory_input="mock")
    vacf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
