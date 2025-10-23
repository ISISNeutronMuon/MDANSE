import numpy as np
import pytest
from MDANSE.MolecularDynamics.Analysis import (AnalysisError,
                                               mean_square_displacement,
                                               mean_square_fluctuation,
                                               radius_of_gyration)

COORDS = [
    np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]], dtype=float),
    np.array([[1, 1, 1], [2, 1, 1], [3, 1, 1]], dtype=float),
    np.array([[1, 1, 1], [2, 1, 1], [8, 1, 1]], dtype=float),
    np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]], dtype=float),
    np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
              [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], dtype=float),
    np.array([[1, 1, 1], [2, 1, 1], [2, 2, 1], [1, 2, 1],
              [1, 1, 2], [2, 1, 2], [2, 2, 2], [1, 2, 2]], dtype=float),
]


@pytest.mark.parametrize("coords, n_configs, expected", [
    (COORDS[1], 1, [0., 1., 4.])
])
def test_mean_square_displacement(coords, n_configs, expected):
    msd = mean_square_displacement(coords, n_configs)
    assert np.allclose(msd, expected)

@pytest.mark.parametrize("coords, root, expected", [
    (COORDS[3], False, 19.625),
    (COORDS[3], True, np.sqrt(19.625)),
    (COORDS[4], False, 0.75),
])
def test_mean_square_fluctuation(coords, root, expected):
    msf = mean_square_fluctuation(coords, root=root)
    assert msf == expected

@pytest.mark.parametrize("coords, masses, root, expected", [
    (COORDS[3], None, False, 19.625),
    (COORDS[3], [1, 1, 5, 1], False, 24.15625),
    (COORDS[3], None, True, np.sqrt(19.625)),
    (COORDS[3], [1, 1, 5, 1], True, np.sqrt(24.15625)),
    (COORDS[4], None, True, np.sqrt(0.75)),
    (COORDS[4], [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], True, np.sqrt(0.5))
])
def test_radius_of_gyration(coords, masses, root, expected):
    rog = radius_of_gyration(coords, masses, root=root)
    assert rog == expected
