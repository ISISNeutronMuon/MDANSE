from typing import Any

import numpy as np
import pytest

from MDANSE_GUI.Plots.Ops.Op import Op
from MDANSE_GUI.Plots.Ops import (
    Abs,
    Exp,
    Ln,
    Normalise,
    Pow,
    Rescale,
    ScaleToRange,
    Shift,
    Truncate,
    GlobalNormalise,
)
from MDANSE_GUI.Tabs.Models.PlottingContext import SingleDataset


@pytest.fixture
def dataset():
    ds = SingleDataset("Fixed", None, data=list(range(-5, 5)))
    ds.set_data_limits("0")
    return ds


@pytest.fixture
def rand_2d_dataset():
    ds = SingleDataset("Rand", None, data=np.random.random((10, 3)))
    ds.set_data_limits("0:3")
    return ds


@pytest.mark.parametrize(
    "op,args,expected",
    [
        (Abs, {}, [5, 4, 3, 2, 1, 0, 1, 2, 3, 4]),
        (
            Exp,
            {},
            [
                6.73794700e-03,
                1.83156389e-02,
                4.97870684e-02,
                1.35335283e-01,
                3.67879441e-01,
                1.00000000e00,
                2.71828183e00,
                7.38905610e00,
                2.00855369e01,
                5.45981500e01,
            ],
        ),
        (Ln, {}, [-np.inf, 0.0, 0.69314718, 1.09861229, 1.38629436]),
        (
            Normalise,
            {"mode": "MAX"},
            [-1.25, -1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0],
        ),
        (
            Normalise,
            {"mode": "ABSMAX"},
            [-1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8],
        ),
        (
            Normalise,
            {"mode": "SUM"},
            [1.0, 0.8, 0.6, 0.4, 0.2, -0.0, -0.2, -0.4, -0.6, -0.8],
        ),
        (
            Normalise,
            {"mode": "AVERAGE"},
            [10.0, 8.0, 6.0, 4.0, 2.0, -0.0, -2.0, -4.0, -6.0, -8.0],
        ),
        (Pow, {"exponent": 2}, [25, 16, 9, 4, 1, 0, 1, 4, 9, 16]),
        (Rescale, {"amount": 2}, [-10, -8, -6, -4, -2, 0, 2, 4, 6, 8]),
        (
            ScaleToRange,
            {"min_val": 0, "max_val": 1},
            [0, 1 / 9, 2 / 9, 3 / 9, 4 / 9, 5 / 9, 6 / 9, 7 / 9, 8 / 9, 1.0],
        ),
        (Shift, {"amount": 1}, [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5]),
        (
            Truncate,
            {"min_val": 0, "max_val": 3, "mode": "VALUE"},
            [-3, -2, -1, 0, 1, 2, 3],
        ),
        (
            Truncate,
            {"min_val": 0, "max_val": 50, "mode": "PERCENT"},
            [-2, -1, 0, 1, 2],
        ),
    ],
)
def test_op(
    op: type[Op], args: dict[str, Any], expected: list[float], dataset: SingleDataset
):
    dataset.ops = [op("0", **args)]

    for _lab, (_x, y) in dataset.curves_vs_axis("index0"):
        assert np.allclose(expected, y)


@pytest.mark.parametrize(
    "op,args",
    [
        (GlobalNormalise, {"mode": "MAX"}),
        (GlobalNormalise, {"mode": "ABSMAX"}),
        (GlobalNormalise, {"mode": "SUM"}),
        (GlobalNormalise, {"mode": "AVERAGE"}),
    ],
)
def test_multidata_op(
    op: type[Op], args: dict[str, Any], rand_2d_dataset: SingleDataset
):
    rand_2d_dataset.ops = [op("0:3", **args)]

    curves = np.array([y for _lab, (_x, y) in rand_2d_dataset.curves_vs_axis("index0")])

    match args["mode"]:
        case "MAX":
            assert np.isclose(curves.max(), 1)
        case "ABSMAX":
            assert np.isclose(np.abs(curves).max(), 1)
        case "SUM":
            assert any(np.isclose(curve.sum(), 1) for curve in curves) and all(
                curve.sum() <= 1.1 for curve in curves
            )
        case "AVERAGE":
            assert any(np.isclose(np.nanmean(curve), 1) for curve in curves) and all(
                np.nanmean(curve) <= 1.1 for curve in curves
            )
