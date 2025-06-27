import tempfile
import os
from os import path

import numpy as np
import h5py
import pytest

from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.paths import CONV_DIR, RESULTS_DIR
from test_helpers.compare_hdf5 import compare_hdf5

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"

@pytest.fixture(scope="module")
def qvector_grid():
    return (
        "GridQVectors",
        {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
    )


@pytest.fixture(scope="module")
def dcsf(tmp_path_factory):
    temp_name = tmp_path_factory.mktemp("data") / "output_dcsf"
    out_file = temp_name.with_suffix(".mda")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_coherent",
    }

    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)

    yield out_file


@pytest.fixture(scope="module")
def disf(tmp_path_factory):
    temp_name = tmp_path_factory.mktemp("data") / "output_disf"
    out_file = temp_name.with_suffix(".mda")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    yield out_file


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_dcsf(tmp_path, traj_info, qvector_grid):
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
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "weights": "b_coherent",
    }

    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"dcsf_{traj_info[0]}.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)"),
                 startswith=True, scale_result=True, scale_benchmark=True,
                 atol=1e-8)


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_ccf(tmp_path, traj_info, qvector_grid):
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
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "weights": "equal",
    }

    ccf = IJob.create("CurrentCorrelationFunction")
    ccf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"ccf_{traj_info[0]}.mda"

    compare_hdf5(out_file, result_file, ("J(q,f)", "j(q,t)"),
                 startswith=True, scale_result=True, scale_benchmark=True,
                 atol=1e-6)


def test_output_axis_preview(tmp_path, qvector_grid):
    temp_name = tmp_path / "output"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
        "q_vectors": qvector_grid,
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_coherent",
    }

    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.setup(parameters)
    axes = dcsf.preview_output_axis()

    print(axes)
    assert len(axes) == 3  # two configurators return valid arrays


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_disf(tmp_path, traj_info, qvector_grid):
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
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "weights": "b_incoherent",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"disf_{traj_info[0]}.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)"),
                 startswith=True, scale_result=True, scale_benchmark=True)


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_eisf(tmp_path, traj_info, qvector_grid):
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
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "weights": "b_incoherent",
    }

    eisf = IJob.create("ElasticIncoherentStructureFactor")
    eisf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"eisf_{traj_info[0]}.mda"
    compare_hdf5(out_file,
                 result_file,
                 ("eisf",),
                 startswith=True,
                 scale_result=True,
                 scale_benchmark=True)


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_gdisf(tmp_path, traj_info):
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
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "weights": "b_incoherent",
    }

    gdisf = IJob.create("GaussianDynamicIncoherentStructureFactor")
    gdisf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"gdisf_{traj_info[0]}.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)", "msd"),
                 startswith=True)


def test_ndtsf(tmp_path, disf, dcsf, qvector_grid):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "disf_input_file": disf,
        "dcsf_input_file": dcsf,
        "trajectory": short_traj,
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
    }

    ndtsf = IJob.create("NeutronDynamicTotalStructureFactor")
    ndtsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / "ndtsf.mda"

    compare_hdf5(out_file, result_file, ("f(q,t)", "s(q,f)"),
                 startswith=True, atol=1e-6)


def test_ssfsf(tmp_path, dcsf):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "dcsf_input_file": dcsf,
        "trajectory": short_traj,
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
    }

    ssfsf = IJob.create("StructureFactorFromScatteringFunction")
    ssfsf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / "sffsf_short_traj.mda"

    compare_hdf5(out_file, result_file, ("ssf_total"), startswith=True,
                 atol=1e-6)

@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
def test_sldp(tmp_path, traj_info):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    text_file = tmp_path / "output_text.tar"

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1),
        "output_files": (temp_name, ("MDAFormat", "TextFormat"), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
        "axis": "c",
        "dr": 0.01,
    }

    sldp = IJob.create("ScatteringLengthDensityProfile")
    sldp.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()
    assert text_file.is_file()

    result_file = RESULTS_DIR / f"sldp_{traj_info[0]}.mda"

    compare_hdf5(out_file, result_file, ("sldp", "sldp_incoherent", "sldp_total", "dp_total"),
                 startswith=True)
