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
from numpy.linalg import det

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


def build_cartesian_axes(origin, p1, p2, dtype=np.float64):
    origin = np.array(origin, dtype=dtype)
    p1 = np.array(p1, dtype=dtype)
    p2 = np.array(p2, dtype=dtype)

    v1 = p1 - origin
    v2 = p2 - origin

    n1 = v1 + v2
    n1 /= np.linalg.norm(n1)

    n3 = np.cross(v1, n1)
    n3 /= np.linalg.norm(n3)

    n2 = np.cross(n3, n1)
    n2 /= np.linalg.norm(n2)

    return n1, n2, n3


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


def random_points_on_disk(axis, radius=1.0, nPoints=100):
    axis = Vector(axis).normal().array

    points = np.random.uniform(-radius, radius, 3 * nPoints)
    points = points.reshape((3, nPoints))

    proj = np.dot(axis, points)
    proj = np.dot(axis[:, np.newaxis], proj[np.newaxis, :])

    points -= proj

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


def get_euler_angles(rotation, tolerance=1e-5):
    """
    R must be an indexable of shape (3,3) and represent and ORTHOGONAL POSITIVE
    DEFINITE matrix.
    """

    fuzz = 1e-3
    rotation = np.asarray(rotation, float)

    if det(rotation) < 0.0:
        raise GeometryError("determinant is negative\n" + str(rotation))

    if not np.allclose(np.mat(rotation) * rotation.T, np.identity(3), atol=tolerance):
        raise GeometryError("not an orthogonal matrix\n" + str(rotation))
    cang = 2.0 - np.sum(
        np.square(
            [
                rotation[0, 2],
                rotation[1, 2],
                rotation[2, 0],
                rotation[2, 1],
                rotation[2, 2],
            ]
        )
    )
    cang = np.sqrt(min(max(cang, 0.0), 1.0))
    if rotation[2, 2] < 0.0:
        cang = -cang
    ang = np.arccos(cang)
    beta = np.degrees(ang)
    sang = np.sin(ang)
    if sang > fuzz:
        alpha = np.degrees(np.arctan2(rotation[1, 2], rotation[0, 2]))
        gamma = np.degrees(np.arctan2(rotation[2, 1], -rotation[2, 0]))
    else:
        alpha = np.degrees(np.arctan2(-rotation[0, 1], rotation[0, 0] * rotation[2, 2]))
        gamma = 0.0

    if np.isclose(beta, 0.0, atol=fuzz):
        alpha, beta, gamma = alpha + gamma, 0.0, 0.0
    elif np.isclose(beta, 180.0, atol=fuzz):
        alpha, beta, gamma = alpha - gamma, 180.0, 0.0

    alpha = np.mod(alpha, 360.0)
    gamma = np.mod(gamma, 360.0)

    if np.isclose(alpha, 360.0, atol=fuzz):
        alpha = 0.0
    if np.isclose(gamma, 360.0, atol=fuzz):
        gamma = 0.0

    return alpha, beta, gamma


def superposition_fit(confs):
    """
    :param confs: the weight, reference position, and alternate position for each atom
    :type confs: sequence of (float, Vector, Vector)
    :returns: the quaternion representing the rotation,
              the center of mass in the reference configuration,
              the center of mass in the alternate configuraton,
              and the RMS distance after the optimal superposition
    """
    w_sum = 0.0
    wr_sum = np.zeros((3,), np.float64)
    for w, r_ref, r in confs:
        w_sum += w
        wr_sum += w * r_ref.array
    ref_cms = wr_sum / w_sum
    pos = np.zeros((3,), np.float64)
    possq = 0.0
    cross = np.zeros((3, 3), np.float64)
    for w_in, r_ref_in, r_in in confs:
        w = w_in / w_sum
        r_ref = r_ref_in.array - ref_cms
        r = r_in.array
        pos = pos + w * r
        possq = possq + w * np.add.reduce(r * r) + w * np.add.reduce(r_ref * r_ref)
        cross = cross + w * r[:, np.newaxis] * r_ref[np.newaxis, :]
    k = np.zeros((4, 4), np.float64)
    k[0, 0] = -cross[0, 0] - cross[1, 1] - cross[2, 2]
    k[0, 1] = cross[1, 2] - cross[2, 1]
    k[0, 2] = cross[2, 0] - cross[0, 2]
    k[0, 3] = cross[0, 1] - cross[1, 0]
    k[1, 1] = -cross[0, 0] + cross[1, 1] + cross[2, 2]
    k[1, 2] = -cross[0, 1] - cross[1, 0]
    k[1, 3] = -cross[0, 2] - cross[2, 0]
    k[2, 2] = cross[0, 0] - cross[1, 1] + cross[2, 2]
    k[2, 3] = -cross[1, 2] - cross[2, 1]
    k[3, 3] = cross[0, 0] + cross[1, 1] - cross[2, 2]
    for i in range(1, 4):
        for j in range(i):
            k[i, j] = k[j, i]
    k = 2.0 * k
    for i in range(4):
        k[i, i] = k[i, i] + possq - np.add.reduce(pos * pos)
    e, v = np.linalg.eig(k)
    v = np.transpose(v)
    i = np.argmin(e)
    v = v[i]
    if v[0] < 0:
        v = -v
    if e[i] <= 0.0:
        rms = 0.0
    else:
        rms = np.sqrt(e[i])

    from MDANSE.Mathematics.LinearAlgebra import Quaternion, Vector

    return Quaternion(v), Vector(ref_cms), Vector(pos), rms
