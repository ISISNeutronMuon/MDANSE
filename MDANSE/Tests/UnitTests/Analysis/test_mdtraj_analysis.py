import numpy as np
import pytest
from numpy.testing import assert_allclose
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


@pytest.mark.parametrize("grouping_level", ["atom", "molecule"])
def test_hydrogen_bonds(generate_benchmarks, tmp_path, parameters, grouping_level,):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"mdtraj_analysis_hbond_{grouping_level}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["mdtraj_analysis"] = ([], {})
    parameters["grouping_level"] = grouping_level
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    job = IJob.create("HydrogenBondStatistics")
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

