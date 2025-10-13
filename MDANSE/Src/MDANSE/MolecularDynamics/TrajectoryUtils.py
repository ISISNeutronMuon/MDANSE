#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import numpy as np

from MDANSE.Core.Error import Error


class MolecularDynamicsError(Error):
    pass


class UniverseAdapterError(Error):
    pass


def atomic_trajectory(
    config: np.ndarray,
    cell: np.ndarray,
    rcell: np.ndarray,
    *,
    box_coordinates: bool = False,
) -> np.ndarray:
    """For the coordinates of a specific atom, remove all unit cell jumps.

    Parameters
    ----------
    config : np.ndarray
        The coordinates for a specific atoms.
    cell : np.ndarray
        The direct matrices.
    rcell : np.ndarray
        The inverse matrices.
    box_coordinates : bool
        Returns the coordinates in fractional coordinates if true.

    Returns
    -------
    np.ndarray
        The input config but the unit cell jumps removed.

    """
    trajectory = np.einsum("ij,ijk->ik", config, rcell)
    sdxyz = trajectory[1:, :] - trajectory[:-1, :]
    sdxyz -= np.cumsum(np.round(sdxyz), axis=0)
    trajectory[1:, :] = trajectory[:-1, :] + sdxyz
    if not box_coordinates:
        trajectory = np.einsum("ij,ijk->ik", trajectory, cell)
    return trajectory
