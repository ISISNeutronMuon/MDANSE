import tempfile
import os
from os import path

import numpy as np
import h5py
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
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
)

com_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "com_trajectory.mdt",
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
    parameters["r_values"] = (0.0, 0.9, 0.1)
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

for tp in [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)]:
    for jt in [
        ("RadiusOfGyration", ["rog"]),
        ("DensityProfile", ["dp"]),
        ("MolecularTrace", [
                "molecular_trace",
                "x_position",
                "y_position",
                "z_position"
        ]),
        ("Eccentricity", ["eccentricity"]),
    ]:
        for rm in [("single-core", 1), ("multicore", -4)]:
            for of in ["MDAFormat", "TextFormat"]:
                total_list.append((tp, jt, rm, of))

for tp in [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)]:
    for jt in [
        ("SolventAccessibleSurface", ["sas"]),
        ("RootMeanSquareDeviation", ["rmsd"]),
        ("RootMeanSquareFluctuation", ["rmsf"]),
        ("Voronoi", ["mean_volume", "neighbourhood_histogram"]),
        ("CoordinationNumber", ["cn"]),
        ("PairDistributionFunction", ["pdf", "rdf", "tcf"]),
        ("StaticStructureFactor", ["ssf"]),
        ("XRayStaticStructureFactor", ["xssf"]),
    ]:
        for rm in [("single-core", 1)]:
            for of in ["MDAFormat"]:
                total_list.append((tp, jt, rm, of))


@pytest.mark.parametrize("traj_info,job_info,running_mode,output_format", total_list)
def test_structure_analysis(
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
        result_file = os.path.join(result_dir, f"structure_analysis_{traj_info[0]}_{job_info[0]}.mda")

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
