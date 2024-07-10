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

mdmc_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "Ar_mdmc_h5md.h5",
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


total_list = []

for tp in (short_traj, mdmc_traj):
    for jt in [
        "RadiusOfGyration",
        "SolventAccessibleSurface",
        "RootMeanSquareDeviation",
        "RootMeanSquareFluctuation",
        "DensityProfile",
        "MolecularTrace",
        "Voronoi",
        "Eccentricity",
    ]:
        for rm in [("single-core", 1), ("multicore", -4)]:
            for of in ["MDAFormat", "TextFormat"]:
                total_list.append((tp, jt, rm, of))


@pytest.mark.parametrize("traj_path,job_type,running_mode,output_format", total_list)
def test_structure_analysis(parameters, traj_path, job_type, running_mode, output_format):
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