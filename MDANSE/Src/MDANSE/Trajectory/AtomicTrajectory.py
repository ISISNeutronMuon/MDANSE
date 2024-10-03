import numpy as np


def atomic_trajectory(config, cell, rcell, box_coordinates=False):
    trajectory = np.einsum("ij,ikj->ik", config, rcell)
    sdxyz = trajectory[1:, :] - trajectory[:-1, :]
    sdxyz -= np.cumsum(np.round(sdxyz), axis=0)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz
    if not box_coordinates:
        trajectory = np.einsum("ij,ikj->ik", trajectory, cell)
    return trajectory
