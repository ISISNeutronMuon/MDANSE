import math
from contextlib import nullcontext as success

import numpy as np
import pytest
from MDANSE.Framework.NewQVectors import (LatticeLinearQVectors,
                                          LinearQVectors, PathSegmentQVectors,
                                          QVectorData)
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from test_helpers.common_fixtures import cell, cubic, orthorhombic, hexagonal

@pytest.mark.parametrize("params, expected", [
    (([1, 0, 0],), success([[0., 0., 0.],
                            [1., 0., 0.],
                            [2., 0., 0.]])),

    (([1, 0, 0], 2.), success([[0., 0., 0.],
                               [2., 0., 0.],
                               [4., 0., 0.]])),

    (([1, 0, 0], 1., [1, 1, 1]), success([[1., 1., 1.],
                                          [2., 1., 1.],
                                          [3., 1., 1.]])),

    (([1, 0, 0, 1], 1., [1, 1, 1]),
     pytest.raises(ValueError, match="must be 3-vectors")),

    (([1, 0, 0], 1., [1, 1, 1, 1]),
     pytest.raises(ValueError, match="must be 3-vectors")),
])
def test_linear(params, expected):
    with expected as val:
        qvec = LinearQVectors(*params)
        results = list(qvec.generate_n(3))
        vals = list(map(QVectorData, val))

        assert results == vals

@pytest.mark.parametrize("cell, params, expected_q, expected_hkl", [
    ("cubic", ([1, 0, 0],),
     [[0, 0, 0], [0.2, 0, 0], [0.4, 0, 0]],
     [[0, 0, 0], [1, 0, 0], [2, 0, 0]]),

    ("cubic", ([1, 0, 0], 2.),
     [[0, 0, 0], [0.4, 0, 0], [0.8, 0, 0]],
     [[0, 0, 0], [2, 0, 0], [4, 0, 0]]),

    ("orthorhombic", ([1, 1, 1],),
     [[0, 0, 0], [0.25, 0.2, 0.16666667], [0.5, 0.4, 0.33333333]],
     [[0, 0, 0], [1, 1, 1], [2, 2, 2]]),

    ("orthorhombic", ([1, 1, 1], 2*math.sqrt(3)),
     [[0, 0, 0], [0.5, 0.4, 0.33333333], [1., 0.8, 0.66666667]],
     [[0, 0, 0], [2, 2, 2], [4, 4, 4]]),

    ("hexagonal", ([1, 1, 1],),
     [[0, 0, 0], [0.18413832, 0.18413832, 0.18413832], [0.36827665, 0.36827665, 0.36827665]],
     [[0, 0, 0], [1, 1, 1], [2, 2, 2]]),

    ("hexagonal", ([1, 1, 1], 2*math.sqrt(3)),
     [[0, 0, 0], [0.36827665, 0.36827665, 0.36827665], [0.7365533, 0.7365533, 0.7365533]],
     [[0, 0, 0], [2, 2, 2], [4, 4, 4]]),
], indirect=["cell"])
def test_lattice_linear(cell, params, expected_q, expected_hkl):
    qvec = LatticeLinearQVectors(cell, *params)
    results = list(qvec.generate_n(3))
    print(results)
    assert all(np.allclose(qvec.q, q) for qvec, q in zip(results, expected_q))
    assert all(np.allclose(qvec.hkl_exact, np.array(hkl))
               for qvec, hkl in zip(results, expected_hkl))

@pytest.mark.parametrize("path, params, expected", [
    (([0, 0, 0], [1, 1, 1]), {"steps": 2},
     success([[0., 0., 0.],
              [0.5, 0.5, 0.5]])),

    (([0, 0, 0], [1, 1, 1]), {"steps": 2, "include_end": True},
     success([[0., 0., 0.],
              [1., 1., 1.]])),

    (([0, 0, 0], [1, 1, 1]), {"steps": 3, "include_end": True},
     success([[0., 0., 0.],
              [0.5, 0.5, 0.5],
              [1., 1., 1.]])),

    (([0, 0, 0], [1, 0, 0]), {"q_step": 0.5, "include_end": False},
     success([[0., 0., 0.],
              [0.5, 0., 0.]])),

    (([0, 0, 0], [1, 0, 0]), {"q_step": 0.5, "include_end": True},
     success([[0., 0., 0.],
              [0.5, 0., 0.],
              [1., 0., 0.]])),

    (([0, 0, 0], [1, 1, 1]), {"q_step": 0.5, "steps": 3},
     pytest.raises(ValueError, match="One of")),

    (([0, 0, 0, 0], [1, 1, 1, 1]), {"q_step": 0.5},
     pytest.raises(ValueError, match="must be 3-vectors")),

])
def test_dispersion(path, params, expected):
    with expected as val:
        qvec = PathSegmentQVectors(*path, **params)
        results = list(qvec)
        vals = list(map(QVectorData, val))

        assert results == vals
