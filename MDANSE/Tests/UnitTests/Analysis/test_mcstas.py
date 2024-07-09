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
    parameters["normalize"] = True
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters


@pytest.mark.xfail(reason="see docstring")
def test_mcstas(parameters):
    """This test will be difficult to run:
    On each platform we need a McStas instrument
    compiled for that specific platform."""
    temp_name = tempfile.mktemp()
    parameters["output_files"] = (temp_name, ("MDAFormat",), True)
    job = IJob.create("McStasVirtualInstrument")
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
