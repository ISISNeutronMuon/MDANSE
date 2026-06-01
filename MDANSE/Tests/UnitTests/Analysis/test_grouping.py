import pytest
import h5py

from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import Trajectory

named_mols = CONV_DIR / "named_molecules.mdt"
four_molecules = CONV_DIR / "four_molecules.mdt"


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
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "trajectory": four_molecules,
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
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "trajectory": four_molecules,
        "weights": "b_incoherent",
        "grouping_level": "molecule",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    yield out_file


def test_trajectory_state():
    traj = Trajectory(named_mols)
    traj.set_selection(set(range(60))-set(range(12,60,3)))
    traj.set_transmutation({0:'B', 3:'B', 6: 'B', 9: 'B'})
    traj.set_grouping("molecule")
    uniq = traj.unique_elements
    print(uniq)
    assert 'C' not in uniq


@pytest.mark.parametrize(
    "traj_info",
    [("", named_mols), ("_four_mols", four_molecules)],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize(
    "job_info",
    [
        ("DensityOfStates", ["dos", "vcf"], "equal", 1e-10, 1e-7),
        ("MeanSquareDisplacement", ["msd"], "equal", 1e-10, 1e-7),
        ("VelocityCorrelationFunction", ["vcf"], "equal", 1e-10, 1e-7),
        ("VanHoveFunctionDistinct", ["vh"], "equal", 1e-10, 1e-7),
        ("VanHoveFunctionSelf", ["vh"], "equal", 1e-10, 1e-7),
        ("PositionCorrelationFunction", ["pcf"], "equal", 1e-10, 1e-7),
        ("PositionPowerSpectrum", ["pcf", "pps"], "equal", 1e-10, 1e-7),
        ("RootMeanSquareDeviation", ["rmsd"], "equal", 1e-10, 1e-7),
        ("CoordinationNumber", ["cn"], "equal", 1e-10, 1e-7),
        ("PairDistributionFunction", ["pdf", "rdf", "tcf"], "equal", 1e-10, 1e-7),
        ("StaticStructureFactor", ["ssf"], "equal", 1e-10, 1e-7),
        ("XRayStaticStructureFactor", ["xssf"], "equal", 1e-10, 1e-7),
        ("DynamicCoherentStructureFactor", ["dcsf"], "b_coherent", 1e-5, 1e-4),
        ("CurrentCorrelationFunction", ["ccf"], "b_coherent", 1e-6, 1e-7),
        ("DynamicIncoherentStructureFactor", ["disf"], "b_incoherent", 1e-10, 1e-7),
        ("ElasticIncoherentStructureFactor", ["eisf"], "b_incoherent", 1e-10, 1e-7),
        (
            "GaussianDynamicIncoherentStructureFactor",
            ["gdisf", "msd"],
            "b_incoherent",
            1e-10,
            1e-7,
        ),
    ],
    ids=lambda x: x[0],
)
def test_analysis(generate_benchmarks, tmp_path, parameters, traj_info, job_info):
    job_type, outputs, weights, atol, rtol = job_info
    temp_name = tmp_path / "output"
    log_file = temp_name.with_suffix(".log")
    out_file = temp_name.with_suffix(".mda")
    result_file = RESULTS_DIR / f"grouping_molecule{traj_info[0]}_{job_type}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["trajectory"] = traj_info[1]
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["weights"] = weights

    job = IJob.create(job_type)
    job.configuration = {key: value for key, value in parameters.items() if key in job.parameters}
    print(job)
    job.run(status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    compare_hdf5(
        out_file, result_file, tuple(outputs), startswith=True, atol=atol, rtol=rtol,
        compare_axis=True
    )
    assert log_file.is_file()


@pytest.mark.parametrize(
    "traj_info",
    [("", named_mols), ("_four_mols", four_molecules)],
    ids=lambda x: x[0],
)
def test_rmsf(generate_benchmarks, tmp_path, parameters, traj_info):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"grouping_each_molecule{traj_info[0]}_RootMeanSquareFluctuation.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["trajectory"] = traj_info[1]
    parameters["grouping_level"] = "molecule"
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    rmsf = IJob.create("RootMeanSquareFluctuation")
    rmsf.configuration = {key: value for key, value in parameters.items() if key in rmsf.parameters}
    rmsf.run(status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file, ["rmsf"], startswith=True, compare_axis=True)


def test_ndtsf(generate_benchmarks, tmp_path, disf, dcsf, qvector_grid):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "grouping_molecule_ndtsf.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "grouping_level": "molecule",
        "disf_input_file": disf,
        "dcsf_input_file": dcsf,
        "trajectory": four_molecules,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
    }

    ndtsf = IJob.create("NeutronDynamicTotalStructureFactor")
    ndtsf.configuration = {key: value for key, value in parameters.items() if key in ndtsf.parameters}
    ndtsf.run(status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file,
        result_file,
        ["ndsf"],
        startswith=True,
        atol=1e-6,
        rtol=1e-4,
        compare_axis=True,
    )


def test_ssfsf(generate_benchmarks, tmp_path, dcsf):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "grouping_molecule_sffsf.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "dcsf_input_file": dcsf,
        "trajectory": four_molecules,
        "grouping_level": "molecule",
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
    }

    ssfsf = IJob.create("StructureFactorFromScatteringFunction")
    ssfsf.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file, result_file, ["ssf"], startswith=True, atol=1e-6, rtol=1e-4,
        compare_axis=True
    )


@pytest.mark.parametrize(
    "job_info",
    [
        ("DensityOfStates", ["dos/isotropic", "vcf/isotropic"], "equal", 1e-10, 1e-7),
        ("PositionPowerSpectrum", ["pcf/isotropic", "pps/isotropic"], "equal", 1e-10, 1e-7),
        ("DynamicCoherentStructureFactor", ["dcsf"], "b_coherent", 1e-6, 1e-6),
    ],
    ids=lambda x: x[0],
)
def test_selection_grouping_transmutation_combined(generate_benchmarks, tmp_path, parameters, job_info):
    job_type, outputs, weights, atol, rtol = job_info
    temp_name = tmp_path / "output"
    log_file = temp_name.with_suffix(".log")
    out_file = temp_name.with_suffix(".mda")
    result_file = RESULTS_DIR / f"grouping_molecule_{job_type}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["atom_selection"] = '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_dummy", "operation_type": "difference"}, "2": {"function_name": "select_atoms", "atom_types": ["O"], "operation_type": "intersection"}, "3": {"function_name": "select_atoms", "index_range": [0, 12], "operation_type": "union"}}'
    parameters['atom_transmutation'] = '{"0": "B", "3": "B", "6": "B", "9": "B"}'
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["weights"] = weights

    job = IJob.create(job_type)
    job.configuration = {key: value for key, value in parameters.items() if key in job.parameters}
    job.run(status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    h5_file = h5py.File(out_file)
    for dset_name in outputs:
        if dset_name == "dcsf":
            assert f"/{dset_name}/C" not in h5_file
            assert f"/{dset_name}/s(q,f)/<C1_O2><C1_O2>/CO" not in h5_file
            assert f"/{dset_name}/s(q,f)/<C1_O2><C1_O2>/CC" not in h5_file
            assert f"/{dset_name}/s(q,f)/<C1_O2><C1_O2>/OO" in h5_file
            assert f"/{dset_name}/s(q,f)/<C1_O2><C1_O2>/BO" in h5_file
            assert f"/{dset_name}/s(q,f)/<C1_O2><C1_O2>/BB" in h5_file
        else:
            assert f"/{dset_name}/C" not in h5_file
            assert f"/{dset_name}/<C1_O2>/O" in h5_file
            assert f"/{dset_name}/<C1_O2>/B" in h5_file
