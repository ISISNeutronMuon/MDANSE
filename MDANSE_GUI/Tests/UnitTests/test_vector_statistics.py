import pytest
import tempfile
import os

import h5py
import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

from MDANSE_GUI.Tabs.Views.PlotDataView import convert_vectors_to_datasets, shell_to_modq

file_name = "qvec_dcsf.mda"

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
    nvec_per_q, _ = convert_vectors_to_datasets(file_qvec)
    assert len(nvec_per_q.data) == len(SHELL_MODQ)
    assert all(nvec_per_q.data == VEC_PER_SHELL)

def test_convert_vectors_to_datasets_bin_padding(file_qvec):
    _, vecs_per_qbin = convert_vectors_to_datasets(file_qvec)
    assert np.allclose(vecs_per_qbin.data[:,0], 0)
    assert np.allclose(vecs_per_qbin.data[:,-1], 0)
    assert np.sum(vecs_per_qbin.data) == VEC_PER_SHELL * len(SHELL_MODQ)
