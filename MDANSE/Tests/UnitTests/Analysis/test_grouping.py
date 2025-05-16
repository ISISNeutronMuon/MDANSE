import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "named_molecules.mdt"


@pytest.fixture(scope="module")
def qvector_grid():
    return (
        "GridQVectors",
        {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
    )


################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {
        # "atom_selection": None,
        # "atom_transmutation": None,
        # "frames": (0, 1000, 1),
        "trajectory": short_traj,
        "running_mode": ("multicore", -4),
        "q_vectors": (
            "SphericalLatticeQVectors",
            {
                "seed": 0,
                "shells": (0, 5.0, 0.5),
                "n_vectors": 100,
                "width": 0.5,
            },
        ),
        "q_values": (0.0, 10.0, 0.1),
        "r_values": (0.0, 0.9, 0.01),
        "per_axis": False,
        "reference_direction": (0, 0, 1),
        "instrument_resolution": ("Gaussian", {"sigma": 1.0, "mu": 0.0}),
        "interpolation_order": 3,
        "projection": None,
        "grouping_level": "average over molecules",
        "weights": "equal",
    }
    return parameters


def test_grouped_disf(tmp_path, qvector_grid):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
        "q_vectors": qvector_grid,
        "grouping_level": "average over molecules",
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent2",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / "grouped_disf_averaged.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)"),
                 startswith=True, scale_result=True, scale_benchmark=True)


def test_eisf(tmp_path, qvector_grid):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1),
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
        "q_vectors": qvector_grid,
        "grouping_level": "average over molecules",
        "trajectory": short_traj,
        "running_mode": ("single-core",),
        "weights": "b_incoherent",
    }

    eisf = IJob.create("ElasticIncoherentStructureFactor")
    eisf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / "grouped_eisf_averaged.mda"
    compare_hdf5(out_file, result_file, ("eisf",), startswith=True)


def test_gdisf(tmp_path):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
        "q_shells": (2.0, 12.2, 2.0),
        "grouping_level": "average over molecules",
        "trajectory": short_traj,
        "running_mode": ("single-core",),
        "weights": "b_incoherent2",
    }

    gdisf = IJob.create("GaussianDynamicIncoherentStructureFactor")
    gdisf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / "grouped_gdisf_averaged.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)", "msd"),
                 startswith=True)



@pytest.mark.parametrize("job_info", [
    ("MeanSquareDisplacement", ["msd"]),
    ("PositionAutoCorrelationFunction", ["pacf"]),
    ("RootMeanSquareDeviation", ["rmsd"]),
], ids=lambda x: x[0])
@pytest.mark.parametrize("running_mode", [("single-core", 1), ("multicore", -4)], ids=lambda x: x[0])
@pytest.mark.parametrize("output_format", ["MDAFormat", "TextFormat"])
@pytest.mark.parametrize("grouping", ["average over molecules", "individual molecules"])
def test_dynamics_analysis(
        tmp_path, parameters, job_info, running_mode, output_format, grouping
):
    temp_name = tmp_path / "output"
    log_file = temp_name.with_suffix(".log")

    parameters["running_mode"] = running_mode
    parameters["grouping_level"] = grouping
    parameters["output_files"] = (temp_name, (output_format,), "INFO")

    job_type, outputs = job_info
    outputs = tuple(outputs)

    job = IJob.create(job_type)
    job.run(parameters, status=True)

    if output_format == "MDAFormat":
        out_file = temp_name.with_suffix(".mda")
        result_file = RESULTS_DIR / f"grouping_{grouping.split()[0]}_{job_type}.mda"

        assert out_file.is_file()

        compare_hdf5(out_file, result_file, outputs, startswith=True)

    elif output_format == "TextFormat":
        out_file = temp_name.parent / (temp_name.stem + "_text.tar")
        assert out_file.is_file()

    assert log_file.is_file()

