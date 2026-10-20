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
from scipy.spatial.transform import Rotation

from MDANSE.util_types import FloatArray


class GeometryError(Exception):
    pass


def get_basis_vectors_from_cell_parameters(
    parameters: tuple[float, float, float, float, float, float],
) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Returns the basis vectors for the simulation cell from the six crystallographic parameters.

    Parameters
    ----------
    parameters : tuple[float, float, float, float, float, float]
        The a, b, c, alpha, beta and gamma of the simulation cell.

    Returns
    -------
    tuple[FloatArray, FloatArray, FloatArray]
        A list of three vectors representing respectively a, b and c basis vectors.
    """

    # The simulation cell parameters.
    a, b, c, alpha, beta, gamma = parameters

    # By construction the a vector is aligned with the x axis.
    e1 = np.array([a, 0.0, 0.0])

    # By construction the b vector is in the xy plane.
    e2 = np.dot(b, [np.cos(gamma), np.sin(gamma), 0.0])

    ex = np.cos(beta)
    ey = (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma)
    e3 = np.dot(c, [ex, ey, np.sqrt(1.0 - ex**2 - ey**2)])

    return (e1, e2, e3)


def center_of_mass(coords: FloatArray, masses: FloatArray | None = None):
    """Computes the center of mass for a set of coordinates and masses

    Parameters
    ----------
    coords : FloatArray
        The input coordinates as an n x 3-array.
    masses : FloatArray, optional
        If not None, the input masses as an n-array.
        If None, the center of gravity is computed.
    """
    return np.average(coords, weights=masses, axis=0)


def moment_of_inertia(
    coords: FloatArray,
    com: FloatArray,
    mass: FloatArray,
) -> FloatArray:
    """Return the moment of inertia of a set of atoms.

    The moment of inertia if given as a 3x3 array, and can be diagonalised
    to determine the primary axes of inertia.

    Parameters
    ----------
    coords : FloatArray
        Coordinates of the atoms.
    com : FloatArray
        Centre of mass of the molecule.
    mass : FloatArray
        Masses of the atoms.

    Returns
    -------
    FloatArray
        3x3 array of the moment of inertia
    """
    x, y, z = (coords - com).T
    xx = np.sum(mass * (y**2 + z**2))
    xy = np.sum(-mass * x * y)
    xz = np.sum(-mass * x * z)
    yy = np.sum(mass * (x**2 + z**2))
    yz = np.sum(-mass * y * z)
    zz = np.sum(mass * (x**2 + y**2))

    moi = np.array(
        [
            [xx, xy, xz],
            [xy, yy, yz],
            [xz, yz, zz],
        ]
    )
    return moi


def generate_sphere_points(n_samples: int) -> FloatArray:
    """Returns list of 3d coordinates of points on a sphere using the
    Golden Section Spiral algorithm.

    Returns coordinates on a sphere with radius=1 and centre=0,0,0.

    Parameters
    ----------
    n_samples : int, optional
        number of points on the sphere, by default 1000

    Returns
    -------
    FloatArray
        (n_samples, 3) array of point coordinates on a sphere
    """

    indices = np.arange(n_samples)
    angle_step = np.pi * (np.sqrt(5.0) - 1.0)  # angle step in radians

    ys = 1 - (indices / (n_samples - 1)) * 2  # y coordinate in [-1, 1] range
    radius = np.sqrt(1 - ys**2)  # circle radius at height y

    theta = angle_step * indices

    xs = np.cos(theta) * radius
    zs = np.sin(theta) * radius

    return np.vstack([xs, ys, zs])
