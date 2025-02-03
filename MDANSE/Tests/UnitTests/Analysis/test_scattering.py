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
com_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "com_trajectory.mdt",
)
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
)


@pytest.fixture(scope="module")
def qvector_grid():
    return ("GridQVectors", {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1})


@pytest.fixture(scope="module")
def dcsf():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0},
    )
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_coherent"
    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)
    yield temp_name + ".mda"
    os.remove(temp_name + ".mda")


@pytest.fixture(scope="module")
def disf():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0},
    )
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)
    yield temp_name + ".mda"
    os.remove(temp_name + ".mda")


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
)
def test_dcsf(traj_info, qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_vectors"] = qvector_grid
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    parameters["weights"] = "b_coherent"
    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, f"dcsf_{traj_info[0]}.mda")
    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        keys = [i for i in desired.keys() if any([j in i for j in ["f(q,t)", "s(q,f)"]])]
        for key in keys:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
)
def test_ccf(traj_info, qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_vectors"] = qvector_grid
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    parameters["weights"] = "equal"
    dcsf = IJob.create("CurrentCorrelationFunction")
    dcsf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, f"ccf_{traj_info[0]}.mda")
    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        keys = [i for i in desired.keys() if any([j in i for j in ["J(q,f)", "j(q,t)"]])]
        for key in keys:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_output_axis_preview(qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_vectors"] = qvector_grid
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_coherent"
    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.setup(parameters)
    axes = dcsf.preview_output_axis()
    print(axes)
    assert len(axes) == 3  # two configurators return valid arrays


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
)
def test_disf(traj_info, qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_vectors"] = qvector_grid
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    parameters["weights"] = "b_incoherent2"
    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, f"disf_{traj_info[0]}.mda")
    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        keys = [i for i in desired.keys() if any([j in i for j in ["f(q,t)", "s(q,f)"]])]
        for key in keys:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
)
def test_eisf(traj_info, qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_vectors"] = qvector_grid
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    parameters["weights"] = "b_incoherent"
    eisf = IJob.create("ElasticIncoherentStructureFactor")
    eisf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, f"eisf_{traj_info[0]}.mda")
    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        keys = [i for i in desired.keys() if "eisf" in i]
        for key in keys:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
)
def test_gdisf(traj_info):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    parameters["q_shells"] = (2.0, 12.2, 2.0)
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = traj_info[1]
    parameters["weights"] = "b_incoherent2"
    gdisf = IJob.create("GaussianDynamicIncoherentStructureFactor")
    gdisf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")

    result_file = os.path.join(result_dir, f"gdisf_{traj_info[0]}.mda")
    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        keys = [i for i in desired.keys() if any([j in i for j in ["f(q,t)", "s(q,f)"]])]
        for key in keys:
            np.testing.assert_array_almost_equal(actual[f"/{key}"], desired[f"/{key}"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_ndtsf(disf, dcsf, qvector_grid):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["disf_input_file"] = disf
    parameters["dcsf_input_file"] = dcsf
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    ndtsf = IJob.create("NeutronDynamicTotalStructureFactor")
    ndtsf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_ssfsf(disf):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["sample_inc"] = disf
    parameters["running_mode"] = ("single-core",)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
    ndtsf = IJob.create("StructureFactorFromScatteringFunction")
    ndtsf.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
