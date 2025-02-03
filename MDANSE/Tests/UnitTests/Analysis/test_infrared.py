import tempfile
import os
from os import path

import h5py
import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "named_molecules.mdt",
)
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
)


def test_dacf_analysis():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 100, 1, 51)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core", 1)
    parameters["trajectory"] = short_traj
    parameters["atom_charges"] = (
        '{"0": 0.72, "1": -0.36, "2": -0.36, "3": 0.72, "4": -0.36, '
        '"5": -0.36, "6": 0.72, "7": -0.36, "8": -0.36, "9": 0.72, '
        '"10": -0.36, "11": -0.36, "12": 0.72, "13": -0.36, "14": -0.36, '
        '"15": 0.72, "16": -0.36, "17": -0.36, "18": 0.72, "19": -0.36, '
        '"20": -0.36, "21": 0.72, "22": -0.36, "23": -0.36, "24": 0.72, '
        '"25": -0.36, "26": -0.36, "27": 0.72, "28": -0.36, "29": -0.36, '
        '"30": 0.72, "31": -0.36, "32": -0.36, "33": 0.72, "34": -0.36, '
        '"35": -0.36, "36": 0.72, "37": -0.36, "38": -0.36, "39": 0.72, '
        '"40": -0.36, "41": -0.36, "42": 0.72, "43": -0.36, "44": -0.36, '
        '"45": 0.72, "46": -0.36, "47": -0.36, "48": 0.72, "49": -0.36, '
        '"50": -0.36, "51": 0.72, "52": -0.36, "53": -0.36, "54": 0.72, '
        '"55": -0.36, "56": -0.36, "57": 0.72, "58": -0.36, "59": -0.36}'
    )
    parameters["molecule_name"] = "C1_O2"
    job = IJob.create("DipoleAutoCorrelationFunction")
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(result_dir, "dacf_analysis.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/dacf"], desired["/dacf"])

    os.remove(temp_name + ".mda")

    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_ir_analysis():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 100, 1, 51)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["derivative_order"] = 3
    parameters["running_mode"] = ("single-core", 1)
    parameters["trajectory"] = short_traj
    parameters["atom_charges"] = (
        '{"0": 0.72, "1": -0.36, "2": -0.36, "3": 0.72, "4": -0.36, '
        '"5": -0.36, "6": 0.72, "7": -0.36, "8": -0.36, "9": 0.72, '
        '"10": -0.36, "11": -0.36, "12": 0.72, "13": -0.36, "14": -0.36, '
        '"15": 0.72, "16": -0.36, "17": -0.36, "18": 0.72, "19": -0.36, '
        '"20": -0.36, "21": 0.72, "22": -0.36, "23": -0.36, "24": 0.72, '
        '"25": -0.36, "26": -0.36, "27": 0.72, "28": -0.36, "29": -0.36, '
        '"30": 0.72, "31": -0.36, "32": -0.36, "33": 0.72, "34": -0.36, '
        '"35": -0.36, "36": 0.72, "37": -0.36, "38": -0.36, "39": 0.72, '
        '"40": -0.36, "41": -0.36, "42": 0.72, "43": -0.36, "44": -0.36, '
        '"45": 0.72, "46": -0.36, "47": -0.36, "48": 0.72, "49": -0.36, '
        '"50": -0.36, "51": 0.72, "52": -0.36, "53": -0.36, "54": 0.72, '
        '"55": -0.36, "56": -0.36, "57": 0.72, "58": -0.36, "59": -0.36}'
    )
    parameters["molecule_name"] = "C1_O2"
    job = IJob.create("Infrared")
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(result_dir, "ir_analysis.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/ddacf"], desired["/ddacf"])
        np.testing.assert_array_almost_equal(actual["/ir"], desired["/ir"])

    os.remove(temp_name + ".mda")

    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
