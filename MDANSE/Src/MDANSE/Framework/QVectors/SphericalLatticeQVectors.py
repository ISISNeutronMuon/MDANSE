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
from scipy.spatial import KDTree

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors
from MDANSE.Framework.QVectors.SphericalQVectors import spherical_vectors


class SphericalLatticeQVectors(LatticeQVectors):
    """Generates randomly-selected lattice vectors grouped into spheres.

    Only vectors commensurate with the reciprocal space lattice will be generated.
    If more lattice vectors than requested are available in the requested range
    for a shell, a subset of the vectors will be selected with the probability
    given as a Gaussian function with FWHM of width/2 and centred on the |q|
    which is the nominal centre of the shell.

    |Q| values for which no valid vectors can be found are omitted in the output.
    Most calculations will produce one data point per |Q| by averaging the results
    over all vectors in the shell.
    """

    settings = {}
    settings["seed"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0, 5.0, 0.5),
        },
    )
    settings["n_samples"] = ("IntegerConfigurator", {"mini": 1, "default": 100000})
    settings["n_vectors"] = ("IntegerConfigurator", {"mini": 1, "default": 100})
    settings["force_equal_weights"] = ("BooleanConfigurator", {"default": False})
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])

        width = self._configuration["width"]["value"]

        nvecs_per_shell = self._configuration["n_vectors"]["value"]
        n_samples = self._configuration["n_samples"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = {}

        for q in self._configuration["shells"]["value"]:
            # 1.2 * (q + width) just to make sure we don't miss any out.
            lattice_hkl_vectors = self.get_reciprocal_lattice_hkl(1.2 * (q + width))
            selection = self.vectors_within_limits(
                self.hkl_to_qvectors(lattice_hkl_vectors, self._unit_cell),
                q_min=q - 0.5 * width,
                q_max=q + 0.5 * width,
            )

            if not np.any(selection):
                self._configuration["q_vectors"][q] = None
                continue

            lattice_hkl_vectors = lattice_hkl_vectors.T[selection].T
            q_vectors = self.hkl_to_qvectors(lattice_hkl_vectors, self._unit_cell)

            selection = fpsampling(q_vectors.T, nvecs_per_shell)
            q_vectors = q_vectors.T[selection].T

            if self._configuration["force_equal_weights"]["value"]:
                weights = np.ones(q_vectors.shape[1])
            else:
                samples = spherical_vectors(q, width, n_samples)
                tree = KDTree(q_vectors.T)
                _, indices = tree.query(samples.T)
                weights = np.bincount(indices, minlength=q_vectors.shape[1])
                weights = q_vectors.shape[1] * weights / n_samples

            self._configuration["q_vectors"][q] = {
                "q_vectors": q_vectors,
                "n_q_vectors": q_vectors.shape[1],
                "weights": weights,
                "q": q,
                "hkls": lattice_hkl_vectors,
            }
            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()


def fpsampling(q_vectors: np.ndarray, n_vecs: int) -> np.ndarray:
    """Basic farthest point sampling function used to sample q-vectors.

    Parameters
    ----------
    q_vectors : np.ndarray
        Array of q_vectors.
    n_vecs : int
        Number of vectors to sample.

    Returns
    -------
    np.ndarray
        Index of selected q-vectors.

    Raises
    ------
    ValueError
        When `n_vecs` is zero or less than zero.
    """
    n_points = q_vectors.shape[0]
    if n_vecs >= n_points:
        return np.arange(n_points)
    elif n_points == 1:
        return np.array([np.random.randint(0, n_points)])
    elif n_points <= 0:
        raise ValueError("n_vecs should be greater than zero.")

    dists = np.full(n_points, np.inf)
    selected = np.random.randint(n_points)
    selection = np.zeros(n_vecs, dtype=int)
    selection[0] = selected

    for i in range(1, n_vecs):
        diff = q_vectors - q_vectors[selected]
        dist_sq = np.sum(diff**2, axis=1)
        dists = np.minimum(dists, dist_sq)
        selected = np.argmax(dists)
        selection[i] = selected

    return selection
