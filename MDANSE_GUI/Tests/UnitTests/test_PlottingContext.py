import pytest
import tempfile
import os

import h5py
import numpy as np

from qtpy import QtGui, QtCore, QtWidgets

from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset

file_1d_name = "super_dos.mda"
file_2d_name = "disf_argon.mda"


@pytest.fixture()
def file_1d():
    tempfile = h5py.File(file_1d_name)
    yield tempfile
    tempfile.close()


@pytest.fixture()
def file_2d():
    tempfile = h5py.File(file_2d_name)
    yield tempfile
    tempfile.close()


def test_single_dataset_1d(file_1d):
    temp = SingleDataset("dos_total", file_1d)
    assert len(temp._data.shape) == 1


def test_single_dataset_2d(file_2d):
    temp = SingleDataset("f(q,t)_total", file_2d)
    assert len(temp._data.shape) == 2


def test_available_x_axes_1d(file_1d):
    temp = SingleDataset("dos_total", file_1d)
    axes = temp.available_x_axes()
    assert axes == ["omega"]
    assert temp._axes_units[axes[0]] == "rad/ps"
    longest = temp.longest_axis()
    assert longest[0] == "rad/ps"


def test_available_x_axes_2d(file_2d):
    temp = SingleDataset("f(q,t)_total", file_2d)
    axes = temp.available_x_axes()
    print(axes)
    assert [temp._axes_units[axis] for axis in axes] == ["1/nm", "ps"]
    longest = temp.longest_axis()
    print(longest)
    assert longest[0] == "ps"


def test_curves_vs_axis_2d_long_axis(file_2d):
    temp = SingleDataset("f(q,t)_total", file_2d)
    temp.set_data_limits("0;1;2;3")
    curves = temp.curves_vs_axis(("ps", "time"), max_limit=12)
    print(len(curves))
    assert len(curves) == 4
    print(curves.keys())
    assert len(curves[(0,)]) == 501


def test_curves_vs_axis_2d_short_axis(file_2d):
    temp = SingleDataset("f(q,t)_total", file_2d)
    temp.set_data_limits("2;3;4;5")
    curves = temp.curves_vs_axis(("1/nm", "q"), max_limit=12)
    print(len(curves))
    assert len(curves) == 4
    print(curves.keys())
    assert len(curves[(2,)]) == 10
