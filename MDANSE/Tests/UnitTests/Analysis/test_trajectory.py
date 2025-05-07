import tempfile
import os
from os import path
import pytest

from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"


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
    parameters["r_values"] = (0.0, 10.0, 0.1)
    parameters["per_axis"] = False
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = "3rd order"
    parameters["projection"] = None
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters

@pytest.mark.parametrize("traj_type", [
    pytest.param("RigidBodyTrajectory",
                 marks=pytest.mark.xfail()),
    pytest.param("GlobalMotionFilteredTrajectory",
                 marks=pytest.mark.xfail()),
    "CroppedTrajectory",
    "CenterOfMassesTrajectory",
    "UnfoldedTrajectory",
])
def test_trajectory(tmp_path, parameters, traj_type):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mdt")
    log_file = temp_name.with_suffix(".log")

    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")

    job = IJob.create(traj_type)
    job.run(parameters, status=True)

    assert out_file.exists()
    assert log_file.exists()
