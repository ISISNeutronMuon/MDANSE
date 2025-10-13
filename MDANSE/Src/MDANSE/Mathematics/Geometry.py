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
from MDANSE.Mathematics.LinearAlgebra import Vector


class GeometryError(Error):
    pass


def get_basis_vectors_from_cell_parameters(parameters):
    """Returns the basis vectors for the simulation cell from the six crystallographic parameters.

    :param parameters: the a, b, c, alpha, bete and gamma of the simulation cell.
    :type: parameters: list of 6 floats

    :return: a list of three Scientific.Geometry.Vector objects representing respectively a, b and c basis vectors.
    :rtype: list
    """

    # The simulation cell parameters.
    a, b, c, alpha, beta, gamma = parameters

    # By construction the a vector is aligned with the x axis.
    e1 = Vector(a, 0.0, 0.0)

    # By construction the b vector is in the xy plane.
    e2 = b * Vector(np.cos(gamma), np.sin(gamma), 0.0)

    e3_x = np.cos(beta)
    e3_y = (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma)
    e3_z = np.sqrt(1.0 - e3_x**2 - e3_y**2)
    e3 = c * Vector(e3_x, e3_y, e3_z)

    return (e1, e2, e3)


def center_of_mass(coords, masses=None):
    """Computes the center of massfor a set of coordinates and masses
    :param coords: the n input coordinates.
    :type coords: (n,3)-np.array
    :param masses: it not None, the n input masses. If None, the center of gravity is computed.
    :type masses: (n,)-np.array
    :return: the center of mass.
    :rtype: (3,)-np.array
    """

    return np.average(coords, weights=masses, axis=0)


center = center_of_mass


def moment_of_inertia(
    coords: np.ndarray,
    com: np.ndarray,
    mass: np.ndarray,
) -> np.ndarray:
    """Return the moment of inertia of a set of atoms.

    The moment of inertia if given as a 3x3 array, and can be diagonalised
    to determine the primary axes of inertia.

    Parameters
    ----------
    coords : np.ndarray
        Coordinates of the atoms.
    com : np.ndarray
        Centre of mass of the molecule.
    mass : np.ndarray
        Masses of the atoms.

    Returns
    -------
    np.ndarray
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


def generate_sphere_points(n: int) -> np.ndarray:
    """Returns list of 3d coordinates of points on a sphere using the
    Golden Section Spiral algorithm.
    """

    inputs = np.arange(int(n))
    points = np.empty([len(inputs), 3])

    inc = np.pi * (3 - np.sqrt(5))

    offset = 2 / float(n)

    y = inputs * offset - 1 + (offset / 2)
    r = np.sqrt(1 - y * y)
    phi = inputs * inc
    points[:, 0] = np.cos(phi) * r
    points[:, 1] = y
    points[:, 2] = np.sin(phi) * r

    return points


def random_points_on_sphere(radius=1.0, nPoints=100):
    points = np.zeros((3, nPoints), dtype=np.float64)

    theta = 2.0 * np.pi * np.random.uniform(nPoints)
    u = np.random.uniform(-1.0, 1.0, nPoints)
    points[0, :] = radius * np.sqrt(1 - u**2) * np.cos(theta)
    points[1, :] = radius * np.sqrt(1 - u**2) * np.sin(theta)
    points[2, :] = radius * u

    return points


def random_points_on_circle(axis, radius=1.0, nPoints=100):
    axis = Vector(axis).normal().array

    points = np.random.uniform(-radius, radius, 3 * nPoints)
    points = points.reshape((3, nPoints))

    proj = np.dot(axis, points)
    proj = np.dot(axis[:, np.newaxis], proj[np.newaxis, :])

    points -= proj

    points *= radius / np.sqrt(np.sum(points**2, axis=0))

    return points
