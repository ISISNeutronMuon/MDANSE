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
    "named_molecules.mdt",
)
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
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
    parameters["molecule_name"] = "C1_O2"
    parameters["axis"] = "ab"
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = "3rd order"
    parameters["projection"] = None
    parameters["normalize"] = True
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters


@pytest.mark.parametrize(
    "job_info",
    [
        ("AreaPerMolecule", ["area_per_molecule"]),
        ("AngularCorrelation", ["ac"]),
    ],
)
def test_structure_analysis(parameters, job_info):
    temp_name = tempfile.mktemp()
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    job = IJob.create(job_info[0])
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(result_dir, f"structure_analysis_{job_info[0]}.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        for key in job_info[1]:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
