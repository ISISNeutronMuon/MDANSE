from contextlib import nullcontext as success
import numpy as np
import pytest
from MDANSE.MolecularDynamics.UnitCell import UnitCell

from MDANSE.Framework.NewQVectors import GridQVectors, QVectorData
from test_helpers.common_fixtures import cell, cubic, orthorhombic, hexagonal

@pytest.mark.parametrize("ranges, expected", [
    (3, success([[0, 3, 1],
                 [0, 3, 1],
                 [0, 3, 1]])),

    ([3], success([[0, 3, 1],
                   [0, 3, 1],
                   [0, 3, 1]])),

    ([[3]], success([[0, 3, 1],
                     [0, 3, 1],
                     [0, 3, 1]])),

    ([1, 3], success([[1, 3, 1],
                      [1, 3, 1],
                      [1, 3, 1]])),

    ([1, 3, 2], success([[1, 3, 2],
                         [1, 3, 2],
                         [1, 3, 2]])),

    ([(1, 3), (2, 4), (3, 6)], success([[1, 3, 1],
                                        [2, 4, 1],
                                        [3, 6, 1]])),

    ([(1, 3, 2), (2, 4, 2), (3, 6, 2)], success([[1, 3, 2],
                                                 [2, 4, 2],
                                                 [3, 6, 2]])),


], ids=["scalar-0d", "scalar-1d", "scalar-2d",
        "single-start-stop", "single-start-stop-step",
        "triple-start-stop", "triple-start-stop-step"])
def test_grid_qvectors_ranges(ranges, expected):
    ranges = GridQVectors._normalise_ranges(ranges)
    with expected as val:
        np.testing.assert_allclose(ranges, val)

@pytest.mark.parametrize("cell, params, expected", [
    (None, {"ranges": 2}, success([[0., 0., 0.],
                                   [0., 0., 1.],
                                   [0., 1., 0.],
                                   [0., 1., 1.],
                                   [1., 0., 0.],
                                   [1., 0., 1.],
                                   [1., 1., 0.],
                                   [1., 1., 1.]]),
     ),

    ("cubic", {"ranges": 2, "hkl": True}, success([[0., 0., 0.],
                                                   [0., 0., 0.2],
                                                   [0., 0.2, 0.],
                                                   [0., 0.2, 0.2],
                                                   [0.2, 0., 0.],
                                                   [0.2, 0., 0.2],
                                                   [0.2, 0.2, 0.],
                                                   [0.2, 0.2, 0.2]]),
     ),

    ("orthorhombic", {"ranges": 2, "hkl": True}, success([[0., 0., 0.],
                                                          [0., 0., 1/6],
                                                          [0., 0.2, 0.],
                                                          [0., 0.2, 1/6],
                                                          [0.25, 0., 0.],
                                                          [0.25, 0., 1/6],
                                                          [0.25, 0.2, 0.],
                                                          [0.25, 0.2, 1/6]]),
     ),

    ("hexagonal", {"ranges": 2, "hkl": True}, success([[0., 0., 0.],
                                                       [0.18413832,  0.18413832, -0.18413832],
                                                       [ 0.18413832, -0.18413832,  0.18413832],
                                                       [0.36827665, 0.        , 0.        ],
                                                       [-0.18413832,  0.18413832,  0.18413832],
                                                       [0.        , 0.36827665, 0.        ],
                                                       [0.        , 0.        , 0.36827665],
                                                       [0.18413832, 0.18413832, 0.18413832]])
     ),

], indirect=["cell"])
def test_grid_qvectors(cell, params, expected):
    qvecs = GridQVectors(**params, lattice=cell)

    with expected as val:
        exp = [QVectorData(exp, cell) for exp in val]
        qvec = list(qvecs.generate())

        assert qvec == exp
