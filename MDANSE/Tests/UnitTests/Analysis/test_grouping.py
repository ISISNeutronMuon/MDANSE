import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR


named_mols = CONV_DIR / "named_molecules.mdt"


@pytest.fixture(scope="module")
def qvector_grid():
    return (
        "GridQVectors",
        {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
    )


@pytest.fixture(scope="function")
def parameters():
    parameters = {
        "trajectory": named_mols,
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "q_shells": (2.0, 12.2, 2.0),
        "r_values": (0.0, 0.9, 0.01),
        "per_axis": False,
        "reference_direction": (0, 0, 1),
        "instrument_resolution": ("Gaussian", {"sigma": 1.0, "mu": 0.0}),
        "interpolation_order": 3,
        "projection": None,
        "grouping_level": "molecule",
    }
    return parameters


@pytest.fixture(scope="module")
def dcsf(tmp_path_factory):
    temp_name = tmp_path_factory.mktemp("data") / "output_dcsf"
    out_file = temp_name.with_suffix(".mda")

    parameters = {
        "output_files": (temp_name, ("MDAFormat", ), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "trajectory": named_mols,
        "weights": "b_coherent",
        "grouping_level": "molecule",
    }

    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)

    yield out_file


@pytest.fixture(scope="module")
def disf(tmp_path_factory):
    temp_name = tmp_path_factory.mktemp("data") / "output_disf"
    out_file = temp_name.with_suffix(".mda")

    parameters = {
        "output_files": (temp_name, ("MDAFormat", ), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "trajectory": named_mols,
        "weights": "b_incoherent2",
        "grouping_level": "molecule",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    yield out_file


@pytest.mark.parametrize("job_info", [
    ("DensityOfStates", ["dos", "vacf"], "equal", 1e-10, 1e-7),
    ("MeanSquareDisplacement", ["msd"], "equal", 1e-10, 1e-7),
    ("VelocityAutoCorrelationFunction", ["vacf"], "equal", 1e-10, 1e-7),
    ("VanHoveFunctionDistinct", ["g(r,t)"], "equal", 1e-10, 1e-7),
    ("VanHoveFunctionSelf", ["g(r,t)"], "equal", 1e-10, 1e-7),
    ("PositionAutoCorrelationFunction", ["pacf"], "equal", 1e-10, 1e-7),
    ("PositionPowerSpectrum", ["pacf", "pps"], "equal", 1e-10, 1e-7),
    ("RootMeanSquareDeviation", ["rmsd"], "equal", 1e-10, 1e-7),
    ("CoordinationNumber", ["cn"], "equal", 1e-10, 1e-7),
    ("PairDistributionFunction", ["pdf", "rdf", "tcf"], "equal", 1e-10, 1e-7),
    ("StaticStructureFactor", ["ssf"], "equal", 1e-10, 1e-7),
    ("XRayStaticStructureFactor", ["xssf"], "equal", 1e-10, 1e-7),
    ("DynamicCoherentStructureFactor", ["f(q,t)", "s(q,f)"], "b_coherent", 1e-6, 1e-6),
    ("CurrentCorrelationFunction", ["J(q,f)", "j(q,t)"], "b_coherent", 1e-6, 1e-7),
    ("DynamicIncoherentStructureFactor", ["f(q,t)", "s(q,f)"], "b_incoherent2", 1e-10, 1e-7),
    ("ElasticIncoherentStructureFactor", ["eisf"], "b_incoherent2", 1e-10, 1e-7),
    ("GaussianDynamicIncoherentStructureFactor", ["f(q,t)", "s(q,f)", "msd"], "b_incoherent2", 1e-10, 1e-7),
], ids=lambda x: x[0])
def test_analysis(
        tmp_path, parameters, job_info
):
    temp_name = tmp_path / "output"
    log_file = temp_name.with_suffix(".log")

    job_type, outputs, weights, atol, rtol = job_info
    parameters["output_files"] = (temp_name, ("MDAFormat", ), "INFO")
    parameters["weights"] = weights

    job = IJob.create(job_type)
    job.run(parameters, status=True)

    out_file = temp_name.with_suffix(".mda")
    result_file = RESULTS_DIR / f"grouping_molecule_{job_type}.mda"
    assert out_file.is_file()
    compare_hdf5(out_file, result_file, tuple(outputs), startswith=True, atol=atol, rtol=rtol)
    assert log_file.is_file()


def test_rmsf(tmp_path, parameters):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters["grouping_level"] = "each molecule"
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    rmsf = IJob.create("RootMeanSquareFluctuation")
    rmsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    result_file = RESULTS_DIR / "grouping_each_molecule_RootMeanSquareFluctuation.mda"
    compare_hdf5(out_file, result_file, "rmsf", startswith=True)


def test_ndtsf(tmp_path, disf, dcsf, qvector_grid):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "grouping_level": "molecule",
        "disf_input_file": disf,
        "dcsf_input_file": dcsf,
        "trajectory": named_mols,
        "output_files": (temp_name, ("MDAFormat", ), "INFO"),
    }

    ndtsf = IJob.create("NeutronDynamicTotalStructureFactor")
    ndtsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    result_file = RESULTS_DIR / "grouping_molecule_ndtsf.mda"
    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)"),
                 startswith=True, atol=1e-6)


def test_ssfsf(tmp_path, dcsf):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "dcsf_input_file": dcsf,
        "trajectory": named_mols,
        "grouping_level": "molecule",
        "output_files": (temp_name, ("MDAFormat", ), "INFO"),
    }

    ssfsf = IJob.create("StructureFactorFromScatteringFunction")
    ssfsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    result_file = RESULTS_DIR / "grouping_molecule_sffsf.mda"
    compare_hdf5(out_file, result_file, "ssf_total", startswith=True,
                 atol=1e-6)
