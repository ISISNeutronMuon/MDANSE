from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pytest

from MDANSE_GUI.Tabs.Views.PlotDataView import (
    convert_vectors_to_datasets,
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


def test_convert_vectors_to_datasets_vecperq(file_qvec):
    nvec_per_q, _, _ = convert_vectors_to_datasets(file_qvec)
    assert len(nvec_per_q.data) == len(SHELL_MODQ)
    assert all(nvec_per_q.data == VEC_PER_SHELL)
