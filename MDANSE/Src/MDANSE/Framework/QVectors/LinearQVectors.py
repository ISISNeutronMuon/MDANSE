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

from MDANSE.Framework.QVectors.IQVectors import IQVectors, truncated_normal_distribution


def linear_vectors(
    q: float,
    q_width: float,
    n_vecs: int,
    axis: npt.NDArray[float],
    rng: np.random.Generator,
):
    """Generate vectors on a line.

    The distribution will be normal in the |q| values around the
    requested |q| with the q_width.

    Parameters
    ----------
    q : float
        The centre of the |q| value distribution.
    q_width : float
        The width of the |q| distribution.
    n_vecs : int
        Number of vectors to generate.
    axis: npt.NDArray[float]
        Defines a line in space on which the vectors are generated.
    rng : np.random.Generator
        A numpy random number generator object.

    Returns
    -------
    npt.NDArray[float]
        A (3,N) array of vectors.
    """
    qmin = max(0.01 * abs(q), q - q_width / 2)
    qmax = q + q_width / 2
    all_radii = truncated_normal_distribution(n_vecs, qmin, qmax, q_width, q, rng=rng)
    fact = np.array(all_radii)[:n_vecs]
    return axis[:, np.newaxis] * fact


class LinearQVectors(IQVectors):
    """Generates vectors randomly on a straight line.

    Most calculations will produce one data point for |Q| by averaging the results
    over all vectors in the group, which is still called a shell.

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
            "default": (0.0, 5.0, 1.0),
        },
    )
    settings["n_vectors"] = ("IntegerConfigurator", {"mini": 1, "default": 50})
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["axis"] = (
        "VectorConfigurator",
        {"normalize": True, "notNull": True, "default": [1, 0, 0], "valueType": float},
    )

    def _generate(self):
        rng = np.random.default_rng(self._configuration["seed"]["value"] or None)

        axis = self._configuration["axis"]["vector"].array

        width = self._configuration["width"]["value"]

        nvecs_per_shell = self._configuration["n_vectors"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = {}

        for q in self._configuration["shells"]["value"]:
            q_vectors = linear_vectors(q, width, nvecs_per_shell, axis, rng)

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
            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
