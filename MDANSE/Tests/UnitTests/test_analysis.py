import numpy as np
import pytest
from MDANSE.MolecularDynamics.Analysis import (AnalysisError,
                                               mean_square_deviation,
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

@pytest.mark.parametrize("coords,masses,root,expected", [
    ((COORDS[1], COORDS[0]), None, False, 20/3),
    ((COORDS[1], COORDS[0]), [3, 10, 1], False, 80/14),
    ((COORDS[2], COORDS[0]), None, True, 5),
    ((COORDS[4], COORDS[5]), None, True, np.sqrt(3)),
    ((COORDS[4], COORDS[5]), None, False, 3),
    ])
def test_mean_square_deviation(coords, masses, root, expected):
    msd = mean_square_deviation(*coords, masses, root)
    assert msd == expected

@pytest.mark.parametrize("coords,masses,root,expected", [
    ([np.zeros((3, 3)), np.zeros((3, 4))], None, False, AnalysisError),
])
def test_invalid(coords, masses, root, expected):
    with pytest.raises(expected):
        mean_square_deviation(*coords, masses, root)

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
