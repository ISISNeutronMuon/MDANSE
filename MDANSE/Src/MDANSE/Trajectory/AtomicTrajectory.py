import numpy as np


def atomic_trajectory(config, cell, rcell, box_coordinates=False):
    trajectory = np.empty((config.shape[0], 3), dtype=np.float64)
    trajectory = np.einsum("ij,ikj->ik", config, rcell[: config.shape[0]])
    sdxyz = trajectory[:-1, :] - trajectory[1:, :]
    sdxyz -= np.round(sdxyz)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz

    if not box_coordinates:
        trajectory = np.einsum("ij,ikj->ik", trajectory, cell[: config.shape[0]])
    return trajectory
