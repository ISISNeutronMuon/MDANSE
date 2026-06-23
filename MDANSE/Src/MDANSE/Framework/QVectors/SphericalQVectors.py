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


def spherical_vectors(
    q: float, q_width: float, n_vecs: int, rng: np.random.Generator
) -> npt.NDArray[float]:
    """Generate vectors on a sphere.

    The distribution should be uniform in angles, and normal in the
    |q| values around the requested |q| with the q_width.

    Parameters
    ----------
    q : float
        The centre of the |q| value distribution.
    q_width : float
        The width of the |q| distribution.
    n_vecs : int
        Number of vectors to generate.
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
    radii = np.array(all_radii)[:n_vecs]
    theta = np.arccos(2 * rng.random(size=n_vecs) - 1)
    phi = 2 * np.pi * rng.random(size=n_vecs)
    return np.vstack(
        (
            radii * np.sin(theta) * np.cos(phi),
            radii * np.sin(theta) * np.sin(phi),
            radii * np.cos(theta),
        ),
    )


@IQVectors.register("SphericalQVectors")
class SphericalQVectors(IQVectors):
    """Generates vectors randomly on a sphere.

    Most calculations will produce one data point for |Q| by averaging the
    results over all vectors in the shell.

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
    settings["width"] = ("FloatConfigurator", {"mini": 0.0, "default": 1.0})

    def _generate(self):
        rng = np.random.default_rng(self._configuration["seed"]["value"] or None)

        width = self._configuration["width"]["value"]

        nvecs_per_shell = self._configuration["n_vectors"]["value"]

        self._configuration["q_vectors"] = {}

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        for q in self._configuration["shells"]["value"]:
            q_vectors = spherical_vectors(q, width, nvecs_per_shell, rng)

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
