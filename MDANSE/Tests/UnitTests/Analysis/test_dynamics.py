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
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)

mdmc_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "Ar_mdmc_h5md.h5",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


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
def test_vacf(trajectory, interp_order, normalise):
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
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")

def test_pps(trajectory):
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
    parameters["r_values"] = (0.0, 1.0, 0.01)
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

for tp in [short_traj, mdmc_traj]:
    for jt in [
        # "AngularCorrelation",
        # "GeneralAutoCorrelationFunction",
        "DensityOfStates",
        "MeanSquareDisplacement",
        "VelocityAutoCorrelationFunction",
        "VanHoveFunctionDistinct",
        "VanHoveFunctionSelf",
        # "OrderParameter",
        "PositionAutoCorrelationFunction",
    ]:
        for rm in [("single-core", 1), ("multicore", -4)]:
            for of in ["MDAFormat", "TextFormat"]:
                total_list.append((tp,jt, rm, of))


@pytest.mark.parametrize("traj_path,job_type,running_mode,output_format", total_list)
def test_dynamics_analysis(parameters, traj_path, job_type, running_mode, output_format):
    temp_name = tempfile.mktemp()
    parameters["trajectory"] = traj_path
    parameters["running_mode"] = running_mode
    parameters["output_files"] = (temp_name, (output_format,), "INFO")
    job = IJob.create(job_type)
    job.run(parameters, status=True)
    if output_format == "MDAFormat":
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
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
