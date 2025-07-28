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

from collections.abc import Sequence

import numpy as np
from scipy.spatial import KDTree

from MDANSE.MolecularDynamics.Trajectory import Trajectory


def select_positions(
    trajectory: Trajectory,
    *,
    frame_number: int = 0,
    position_minimum: Sequence[float] | None = None,
    position_maximum: Sequence[float] | None = None,
    **_kwargs: str,
) -> set[int]:
    """Select atoms based on their positions at a specified frame number.

    Lower and upper limits of x, y and z coordinates can be given as input.

    Parameters
    ----------
    trajectory : Trajectory
        a trajectory instance in which the atoms are being selected
    frame_number : int, optional
        trajectory frame at which to check the coordinates, by default 0
    position_minimum : Sequence[float], optional
        (x, y, z) lower limits of coordinates to be selected, by default None
    position_maximum : Sequence[float], optional
        (x, y, z) upper limits of coordinates to be selected, by default None

    Returns
    -------
    set[int]
        indicies of atoms with coordinates within limits

    """
    coordinates = trajectory.coordinates(frame_number)
    lower_limits = (
        np.array(position_minimum)
        if position_minimum is not None
        else np.array([-np.inf] * 3)
    )
    upper_limits = (
        np.array(position_maximum)
        if position_maximum is not None
        else np.array([np.inf] * 3)
    )
    valid = np.where(
        ((coordinates > lower_limits) & (coordinates < upper_limits)).all(axis=1)
    )
    return set(valid[0])


def select_sphere(
    trajectory: Trajectory,
    *,
    frame_number: int = 0,
    sphere_centre: Sequence[float],
    sphere_radius: float,
    **_kwargs: str,
) -> set[int]:
    """Select atoms within a sphere.

    Selects atoms at a given distance from a fixed point in space,
    based on coordinates at a specific frame number.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied
    frame_number : int, optional
        trajectory frame at which to check the coordinates, by default 0
    sphere_centre : Sequence[float]
        (x, y, z) coordinates of the centre of the selection
    sphere_radius : float
        distance from the centre within which to select atoms

    Returns
    -------
    set[int]
        set of indices of atoms inside the sphere

    """
    coordinates = trajectory.coordinates(frame_number)
    kdtree = KDTree(coordinates)
    indices = kdtree.query_ball_point(sphere_centre, sphere_radius)
    return set(indices)
