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
