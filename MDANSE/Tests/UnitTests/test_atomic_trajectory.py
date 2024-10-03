import numpy as np
import pytest
from MDANSE.Trajectory.AtomicTrajectory import atomic_trajectory
# from MDANSE.Extensions import atomic_trajectory

cells = np.array([np.eye(3)]*5)

def test_constant():
    coords = np.zeros((5, 3)) + 0.5
    atomic_traj = atomic_trajectory(coords, cells, cells, False)
    assert np.allclose(atomic_traj, 0.5)


def test_one_big_jump():
    coords = np.zeros((5, 3)) + 3.2
    coords[0, 0] = 0.1
    atomic_traj = atomic_trajectory(coords, cells, cells, False)
    result = np.zeros((5, 3)) + 3.2
    result[0, 0] = 0.1
    result[1:, 0] = 0.2
    assert np.allclose(atomic_traj, result)





