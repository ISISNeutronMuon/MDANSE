import numpy as np
import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"
nonorth_traj = CONV_DIR / "nonorthogonal_cell.mdt"


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
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters

@pytest.mark.parametrize("traj_info", [
    ("short_traj", short_traj),
    ("mdmc_traj", mdmc_traj),
    ("com_traj", com_traj),
], ids=lambda x: x[0])
@pytest.mark.parametrize("job_info", [
        ("SolventAccessibleSurface", ["sas"]),
        ("RootMeanSquareDeviation", ["rmsd"]),
        ("RootMeanSquareFluctuation", ["rmsf"]),
        ("Voronoi", ["mean_volume", "neighbourhood_histogram"]),
        ("CoordinationNumber", ["cn"]),
        ("PairDistributionFunction", ["pdf", "rdf", "tcf"]),
        ("StaticStructureFactor", ["ssf"]),
        ("XRayStaticStructureFactor", ["xssf"]),
], ids=lambda x: x[0])
@pytest.mark.parametrize("running_mode", [("single-core", 1)], ids=lambda x: x[0])
@pytest.mark.parametrize("output_format", ["MDAFormat"])
def test_structure_analysis(
        tmp_path, parameters, traj_info, job_info, running_mode, output_format
):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    job_type, outputs = job_info

    parameters["trajectory"] = traj_info[1]
    parameters["running_mode"] = running_mode
    parameters["output_files"] = (temp_name, (output_format,), "INFO")

    job = IJob.create(job_info[0])
    job.run(parameters, status=True)

    if output_format == "MDAFormat":
        out_file = temp_name.with_suffix(".mda")
        result_file = RESULTS_DIR / f"structure_analysis_{traj_info[0]}_{job_type}.mda"

        assert out_file.is_file()

        compare_hdf5(out_file, result_file, tuple(outputs), startswith=True)

    elif output_format == "TextFormat":
        out_file = temp_name.parent / (temp_name.stem + "_text.tar")
        assert out_file.is_file()

    assert log_file.is_file()

@pytest.mark.parametrize("traj_info", [
    ("short_traj", short_traj),
    ("mdmc_traj", mdmc_traj),
    ("com_traj", com_traj),
    ("nonorthogonal_cell", nonorth_traj)
], ids=lambda x: x[0])
def test_pdf_is_zero_at_low_distances(
        tmp_path, parameters, traj_info,
):
    temp_name = tmp_path / "output"

    job_type = "PairDistributionFunction"

    parameters["trajectory"] = traj_info[1]
    parameters["r_values"] = (0.0, 0.5, 0.01)
    parameters["output_files"] = (temp_name, ("FileInMemory",), "no logs")

    print(parameters)
    job = IJob.create(job_type)
    job.run(parameters, status=True)
    results = job.results
    
    print(results.keys())

    assert "pdf_total" in results
    x_axis = results['r'][:]
    y_axis = results['pdf_total'][:]
    banned_range = y_axis[np.where(x_axis<0.05)]
    assert np.allclose(banned_range, 0.0)

    
