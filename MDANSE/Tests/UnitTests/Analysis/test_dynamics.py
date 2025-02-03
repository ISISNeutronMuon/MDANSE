import tempfile
import os
from os import path

import h5py
import numpy as np
import pytest

from MDANSE.Framework.Jobs.IJob import IJob


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "short_trajectory_after_changes.mdt",
)
mdmc_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "Ar_mdmc_h5md.h5",
)
com_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "com_trajectory.mdt",
)
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
    parameters["trajectory"] = short_traj
    vacf = IJob.create("VelocityAutoCorrelationFunction")
    vacf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    if normalise:
        fname = f"vacf_{interp_order}_normalised.mda"
    else:
        fname = f"vacf_{interp_order}.mda"

    result_file = os.path.join(result_dir, fname)

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/vacf_Cu"], desired["/vacf_Cu"])
        np.testing.assert_array_almost_equal(actual["/vacf_S"], desired["/vacf_S"])
        np.testing.assert_array_almost_equal(actual["/vacf_Sb"], desired["/vacf_Sb"])
        np.testing.assert_array_almost_equal(actual["/vacf_total"], desired["/vacf_total"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_pps():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1, 5)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    pps = IJob.create("PositionPowerSpectrum")
    pps.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, "pps.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/pacf_Cu"], desired["/pacf_Cu"])
        np.testing.assert_array_almost_equal(actual["/pacf_S"], desired["/pacf_S"])
        np.testing.assert_array_almost_equal(actual["/pacf_Sb"], desired["/pacf_Sb"])
        np.testing.assert_array_almost_equal(actual["/pacf_total"], desired["/pacf_total"])
        np.testing.assert_array_almost_equal(actual["/pps_Cu"], desired["/pps_Cu"])
        np.testing.assert_array_almost_equal(actual["/pps_S"], desired["/pps_S"])
        np.testing.assert_array_almost_equal(actual["/pps_Sb"], desired["/pps_Sb"])
        np.testing.assert_array_almost_equal(actual["/pps_total"], desired["/pps_total"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {}
    # parameters['atom_selection'] = None
    # parameters['atom_transmutation'] = None
    # parameters['frames'] = (0, 1000, 1)
    parameters["trajectory"] = short_traj
    parameters["running_mode"] = ("multicore", -4)
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {
            "seed": 0,
            "shells": (0, 5.0, 0.5),
            "n_vectors": 100,
            "width": 0.5,
        },
    )
    parameters["q_values"] = (0.0, 10.0, 0.1)
    parameters["r_values"] = (0.0, 0.9, 0.01)
    parameters["per_axis"] = False
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = 3
    parameters["projection"] = None
    parameters["normalize"] = True
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters


total_list = []

for tp in [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)]:
    for jt in [
        # "AngularCorrelation",
        # "GeneralAutoCorrelationFunction",
        ("DensityOfStates", ["dos", "vacf"]),
        ("MeanSquareDisplacement", ["msd"]),
        ("VelocityAutoCorrelationFunction", ["vacf"]),
        ("VanHoveFunctionDistinct", ["g(r,t)"]),
        ("VanHoveFunctionSelf", ["g(r,t)"]),
        # "OrderParameter",
        ("PositionAutoCorrelationFunction", ["pacf"]),
        ("PositionPowerSpectrum", ["pacf", "pps"]),
    ]:
        for rm in [("single-core", 1), ("multicore", -4)]:
            for of in ["MDAFormat", "TextFormat"]:
                total_list.append((tp, jt, rm, of))


@pytest.mark.parametrize("traj_info,job_info,running_mode,output_format", total_list)
def test_dynamics_analysis(
    parameters, traj_info, job_info, running_mode, output_format
):
    temp_name = tempfile.mktemp()
    parameters["trajectory"] = traj_info[1]
    parameters["running_mode"] = running_mode
    parameters["output_files"] = (temp_name, (output_format,), "INFO")
    job = IJob.create(job_info[0])
    job.run(parameters, status=True)
    if output_format == "MDAFormat":
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
        result_file = os.path.join(result_dir, f"dynamics_analysis_{traj_info[0]}_{job_info[0]}.mda")

        with h5py.File(temp_name + ".mda") as actual, h5py.File(result_file) as desired:
            keys = [i for i in desired.keys() if any([j in i for j in job_info[1]])]
            for key in keys:
                np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

        os.remove(temp_name + ".mda")
    elif output_format == "TextFormat":
        assert path.exists(temp_name + "_text.tar")
        assert path.isfile(temp_name + "_text.tar")
        os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_output_axis_preview(parameters):
    temp_name = tempfile.mktemp()
    parameters["running_mode"] = ("single-core", 1)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    job = IJob.create("DensityOfStates")
    job.setup(parameters)
    axes = job.preview_output_axis()
    assert len(axes) == 2  # two configurators return valid arrays
