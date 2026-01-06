from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pytest

from MDANSE_GUI.Tabs.Views.PlotDataView import (
    qvector_binning_general,
    vector_q_statistics_datasets,
    shell_to_modq,
)

WORK_DIR = Path(__file__).parent

file_name = WORK_DIR / "qvec_dcsf.mda"


VEC_PER_SHELL = 20
SHELL_MODQ = (10, 20, 30, 40, 50)


@pytest.fixture()
def file_qvec():
    tempfile = h5py.File(file_name)
    yield tempfile
    tempfile.close()


def test_shell_to_modq_nvectors(file_qvec):
    vec_dataset = file_qvec["vector_generator"]
    for n in range(5):
        modq = shell_to_modq(n, vec_dataset)
        assert len(modq) == VEC_PER_SHELL


def test_shell_to_modq_lengths(file_qvec):
    vec_dataset = file_qvec["vector_generator"]
    for n in range(5):
        modq = shell_to_modq(n, vec_dataset)
        assert np.allclose(modq, SHELL_MODQ[n], atol=0.01, rtol=0.05)


def test_vector_q_statistics_datasets_vecperq(file_qvec):
    nvec_per_q, _, _ = vector_q_statistics_datasets(file_qvec)
    assert len(nvec_per_q.data) == len(SHELL_MODQ)
    assert all(nvec_per_q.data == VEC_PER_SHELL)


@pytest.mark.parametrize("width", [0.1, 1.0, 10.0])
def test_bin_limits_vs_width(width: float):
    binning = qvector_binning_general(5.0, 6.0, 1.0, width, 10)
    bin_min, bin_max = np.min(binning), np.max(binning)
    print(bin_min, bin_max, 1.0, width)
    assert np.isclose(bin_max, 6 + width/2) or bin_max >= 6 + width/2
    assert np.isclose(bin_min, 5 - width/2) or bin_min <= 5 - width/2 or sum(binning < 0) < 2
