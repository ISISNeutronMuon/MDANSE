import tempfile
import os
from os import path

import h5py
import numpy as np
import pytest

from MDANSE.Framework.Jobs.IJob import IJob


file_wd = os.path.dirname(os.path.realpath(__file__))
mock_json = os.path.join(file_wd, "..", "Data", "mock.json")
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
)


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
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["normalize"] = normalise
    parameters["trajectory"] = mock_json
    vacf = IJob.create("VelocityAutoCorrelationFunction", trajectory_input="mock")
    vacf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    if normalise:
        fname = f"mock_traj_vacf_{interp_order}_normalised.mda"
    else:
        fname = f"mock_traj_vacf_{interp_order}.mda"

    result_file = os.path.join(result_dir, fname)

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/vacf_H"], desired["/vacf_H"])
        np.testing.assert_array_almost_equal(actual["/vacf_O"], desired["/vacf_O"])
        np.testing.assert_array_almost_equal(actual["/vacf_Si"], desired["/vacf_Si"])
        np.testing.assert_array_almost_equal(actual["/vacf_total"], desired["/vacf_total"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
