import tempfile
import os
from os import path
import pytest

import numpy as np
import h5py

from MDANSE.Framework.Jobs.IJob import IJob


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "short_trajectory_after_changes.mdt",
)
com_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "com_trajectory.mdt",
)
mdmc_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "Ar_mdmc_h5md.h5",
)
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
)



@pytest.mark.parametrize(
    "traj_info,interp_order",
    [
        (("short_traj", short_traj), 1),
        (("short_traj", short_traj), 3),
        (("mdmc_traj", mdmc_traj), 1),
        (("mdmc_traj", mdmc_traj), 3),
        (("com_traj", com_traj), 1),
        (("com_traj", com_traj), 3)
    ],
)
def test_temperature(traj_info, interp_order):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["interpolation_order"] = interp_order
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    temp = IJob.create("Temperature")
    temp.run(parameters, status=True)

    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(
        result_dir, f"temperature_{traj_info[0]}_{interp_order}.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/kinetic_energy"], desired["/kinetic_energy"])
        np.testing.assert_array_almost_equal(actual["/temperature"], desired["/temperature"])
        np.testing.assert_array_almost_equal(actual["/avg_kinetic_energy"], desired["/avg_kinetic_energy"])
        np.testing.assert_array_almost_equal(actual["/avg_temperature"], desired["/avg_temperature"])

    os.remove(temp_name + ".mda")

    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


@pytest.mark.parametrize(
    "traj_info,output_format",
    [
        (("short_traj", short_traj), "MDAFormat"),
        (("short_traj", short_traj), "TextFormat"),
        (("mdmc_traj", mdmc_traj), "MDAFormat"),
        (("mdmc_traj", mdmc_traj), "TextFormat"),
        (("com_traj", com_traj), "MDAFormat"),
        (("com_traj", com_traj), "TextFormat")
    ],
)
def test_density(traj_info, output_format):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, (output_format,), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    den = IJob.create("Density")
    den.run(parameters, status=True)
    if output_format == "MDAFormat":
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
        result_file = os.path.join(result_dir, f"density_{traj_info[0]}.mda")

        with h5py.File(temp_name + ".mda") as actual, h5py.File(result_file) as desired:
            np.testing.assert_array_almost_equal(actual["/atomic_density"], desired["/atomic_density"])
            np.testing.assert_array_almost_equal(actual["/mass_density"], desired["/mass_density"])
            np.testing.assert_array_almost_equal(actual["/avg_atomic_density"], desired["/avg_atomic_density"])
            np.testing.assert_array_almost_equal(actual["/avg_mass_density"], desired["/avg_mass_density"])

        os.remove(temp_name + ".mda")
    elif output_format == "TextFormat":
        assert path.exists(temp_name + "_text.tar")
        assert path.isfile(temp_name + "_text.tar")
        os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
