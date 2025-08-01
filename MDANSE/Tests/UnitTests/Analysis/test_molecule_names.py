import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "named_molecules.mdt"


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
    parameters["polynomial_order"] = 1
    parameters["molecule_name"] = "C1_O2"
    parameters["molecule_and_axis"] = ("C1_O2", 0)
    parameters["axis"] = "ab"
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = "3rd order"
    parameters["projection"] = None
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters


@pytest.mark.parametrize(
    "job_info",
    [
        ("AreaPerMolecule", ["apm/area_per_molecule"]),
    ], ids=lambda x: x[0],
)
def test_structure_analysis(generate_benchmarks, tmp_path, parameters, job_info):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"structure_analysis_{job_info[0]}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    job = IJob.create(job_info[0])
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file, job_info[1], compare_axis=True)

