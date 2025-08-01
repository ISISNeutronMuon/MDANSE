import numpy as np
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

short_traj = CONV_DIR / "named_molecules.mdt"


def test_dacf_analysis(generate_benchmarks, tmp_path):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "dacf_analysis.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 100, 1, 51),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core", 1),
        "trajectory": short_traj,
        "atom_charges": (
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
        ),
        "molecule_name": "C1_O2",
    }

    job = IJob.create("DipoleAutoCorrelationFunction")
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file, ("/dacf/dacf",), scale_result=True, compare_axis=True)


def test_ir_analysis(generate_benchmarks, tmp_path):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "ir_analysis.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 100, 1, 51),
        "instrument_resolution": ("Gaussian", {"sigma": 1.0, "mu": 0.0}),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "derivative_order": 3,
        "running_mode": ("single-core", 1),
        "trajectory": short_traj,
        "atom_charges": (
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
        ),
        "molecule_name": "C1_O2",
    }

    job = IJob.create("Infrared")
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file, ("/ddacf/ddacf", "/ir/ir"), scale_result=True, compare_axis=True)
