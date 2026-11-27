import numpy as np
import numpy.testing as npt
import pytest
from MDANSE.Mathematics.Signal import differentiate, differentiate_many

mock_trajectory = np.vstack([
    np.sin(np.arange(30)), np.cos(np.arange(30)), np.sin(np.arange(30)/2.1)
]).T

mock_3D_trajectory = np.arange(1,5).reshape((1,4,1)) * mock_trajectory.reshape((30,1,3))


@pytest.fixture(scope="module")
def diff_result():
    result = np.empty_like(mock_3D_trajectory)
    for j in range(mock_3D_trajectory.shape[1]):
        for k in range(mock_3D_trajectory.shape[2]):
            result[:, j, k] = differentiate(mock_3D_trajectory[:, j ,k], order=3)
    return result


def test_result_shape(diff_result):
    new_result = differentiate_many(mock_3D_trajectory, order=3)
    assert diff_result.shape == new_result.shape


def test_result_values(diff_result, output_plots: bool = False):
    new_result = differentiate_many(mock_3D_trajectory, order=3)
    if output_plots:
        import matplotlib.pyplot as mpl
        for j in range(mock_3D_trajectory.shape[1]):
            for k in range(mock_3D_trajectory.shape[2]):
                mpl.plot(np.arange(30), diff_result[:, j,k], label="old MDANSE")
                mpl.plot(np.arange(30), new_result[:, j,k], label = "new scipy")
                mpl.legend(loc=0)
                mpl.savefig(f"derivative_comparison_{j}_{k}.png")
                mpl.close()
    npt.assert_allclose(diff_result, new_result)


@pytest.mark.parametrize("order", [1, 2, 3, 4, 5])
def test_differentiate_many_matches_differentiate(order):
    expected = np.empty_like(mock_3D_trajectory)
    for j in range(mock_3D_trajectory.shape[1]):
        for k in range(mock_3D_trajectory.shape[2]):
            expected[:, j, k] = differentiate(mock_3D_trajectory[:, j, k], dt=0.5, order=order)
    actual = differentiate_many(mock_3D_trajectory, dt=0.5, order=order)
    npt.assert_allclose(actual, expected)


def test_differentiate_many_order_5_exact_polynomial():
    dt = 0.25
    t = np.arange(10, dtype=np.float64) * dt
    # Degree-5 polynomial: 5th-order finite difference recovers exact derivative at all points.
    poly = (t**5 - 2.0 * t**3 + 3.0 * t)[:, None, None]
    expected = (5.0 * t**4 - 6.0 * t**2 + 3.0)[:, None, None]
    actual = differentiate_many(poly, dt=dt, order=5)
    npt.assert_allclose(actual, expected, rtol=1e-11, atol=1e-11)
