from __future__ import annotations

import numpy as np
import pytest
from numpy.testing import assert_allclose
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.ReorientationalTimeCorrelationFunction import (
    correlate,
    correlate_legendre,
)

short_traj = CONV_DIR / "named_molecules.mdt"


@pytest.fixture()
def vector_array():
    return np.array(
        [
            [0.5, 0.5, 0.0],
            [0.6, 0.6, 0.6],
            [0.2, 0.2, 0.7],
            [0.3, 0.3, 0.3],
            [0.5, 0.5, 0.0],
            [0.2, 0.2, 0.7],
            [0.6, 0.6, 0.6],
            [0.3, 0.3, 0.3],
            [0.3, 0.3, 0.3],
            [0.5, 0.5, 0.0],
            [0.6, 0.6, 0.6],
            [0.2, 0.2, 0.7],
        ]
    )


def test_manual_correlation_l1(vector_array):
    n_configs = 7
    diff = vector_array
    ac_fft = correlate(diff, diff[:n_configs], mode="valid") / n_configs
    result_fft = ac_fft.T[0]
    result_manual = correlate_legendre(diff, corr_window=n_configs, poly_order=1)
    assert_allclose(result_fft, result_manual)


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


@pytest.mark.parametrize("polynomial_order", [1, 2, 3])
def test_rtcf(generate_benchmarks, tmp_path, parameters, polynomial_order):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"structure_analysis_rtcf_l{polynomial_order!s}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["legendre_order"] = polynomial_order
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    job = IJob.create("ReorientationalTimeCorrelationFunction")
    job.configuration = {
        key: value for key, value in parameters.items() if key in job.parameters
    }
    job.run(status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file,
        result_file,
        [f"rtcf/l={pord}" for pord in job.legendre_orders],
        compare_axis=True,
    )
