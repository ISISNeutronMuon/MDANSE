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
import numpy.typing as npt
from scipy.spatial.transform import Rotation

from MDANSE.Framework.QVectors.IQVectors import IQVectors, truncated_normal_distribution


def circle_rotation_matrix(
    target_circle_axis: npt.NDArray[float],
) -> npt.NDArray[float] | None:
    """Return rotation matrix that transforms 001 vector into target vector.

    Parameters
    ----------
    target_circle_axis : npt.NDArray[float]
        A 3D vector defining the axis of a circle.

    Returns
    -------
    npt.NDArray[float]
        a 3x3 rotation matrix
    """
    try:
        rotation, _ = Rotation.align_vectors(target_circle_axis, np.array([0, 0, 1]))
    except ValueError:
        return None
    return rotation.as_matrix()


def circle_of_vectors(
    q: float,
    q_width: float,
    n_vecs: int,
    rot_mat: npt.NDArray[float] | None,
) -> npt.NDArray[float]:
    """Generate vectors on a circle in plane.

    The distribution of angles of the vectors on a circle is uniform.
    The distribution of vector length is normal, within q_width around q.

    Parameters
    ----------
    q : float
        Mean |Q| of the vectors in the circle.
    q_width : float
        Spread of |Q| of the generated vectors.
    n_vecs : int
        Number of vectors to generate.
    rot_mat : npt.NDArray[float] | None
        Rotation matrix to be applied to the generated points.

    Returns
    -------
    npt.NDArray[float]
        Array of 3D vectors in a circle with an arbitrary orientation.
    """
    parameter_points = np.random.uniform(0.0, 2 * np.pi, n_vecs)
    regular_circle = np.vstack(
        (
            np.sin(parameter_points),
            np.cos(parameter_points),
            np.zeros_like(parameter_points),
        ),
    )
    if rot_mat is not None:
        regular_circle = np.dot(rot_mat, regular_circle)
    qmin = max(0.01 * abs(q), q - q_width / 2)
    qmax = q + q_width / 2
    all_radii = truncated_normal_distribution(n_vecs, qmin, qmax, q_width, q)
    return np.array(all_radii)[None, :n_vecs] * regular_circle


class CircularQVectors(IQVectors):
    """Generates Q vectors as concentric circles on a plane.

    Vectors will be generated as shells of vectors of similar lengths
    and random orientations on a plane perpendicular to the 'axis' vector.

    The vector lengths in a single shell assume a normal distribution with the
    FWHM of 'width'/2 and limited to the range of (q - width/2, q + width/2)
    around the shell centre defined by the 'shells' input.
    """

    settings = {}
    settings["seed"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0.0, 5.0, 0.5),
        },
    )
    settings["n_vectors"] = ("IntegerConfigurator", {"mini": 1, "default": 50})
    settings["width"] = ("FloatConfigurator", {"mini": 0.0, "default": 1.0})
    settings["axis"] = (
        "VectorConfigurator",
        {"normalize": True, "notNull": True, "default": [0, 0, 1], "valueType": float},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])

        nvecs_per_shell = self._configuration["n_vectors"]["value"]
        target_circle_axis = self._configuration["axis"]["value"] / np.linalg.norm(
            self._configuration["axis"]["value"],
        )
        rot_mat = circle_rotation_matrix(target_circle_axis)

        width = self._configuration["width"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = {}

        for q in self._configuration["shells"]["value"]:
            q_vectors = circle_of_vectors(q, width, nvecs_per_shell, rot_mat=rot_mat)
            self._configuration["q_vectors"][q] = {
                "q_vectors": q_vectors,
                "n_q_vectors": nvecs_per_shell,
                "n_q_found": nvecs_per_shell,
                "weights": np.ones(nvecs_per_shell),
                "q": q,
                "hkls": self.qvectors_to_hkl(q_vectors, self._unit_cell)
                if self._unit_cell is not None
                else None,
            }
