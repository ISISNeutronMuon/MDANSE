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

import random
from functools import partial

import numpy as np
from scipy.spatial import KDTree

from MDANSE.Framework.Parameters import (
    Boolean,
    Float,
    Integer,
    Range,
)
from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors, fpsampling
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

    seed = Integer(minimum=0, default=0)
    shells = Range[float](minimum=0.0, default=(0, 5.0, 0.5), include_last=True)
    n_samples = Integer(minimum=1, default=50_000)
    n_vectors = Integer(minimum=1, default=100)
    force_equal_weights = Boolean()
    width = Float(minimum=1e-6, default=1.0)

    def _generate(self):
        rng = np.random.default_rng(self.seed or None)

        width = self._configuration["width"]["value"]

        nvecs_per_shell = self._configuration["n_vectors"]["value"]
        n_samples = self._configuration["n_samples"]["value"]

        if self._status is not None:
            self._status.start(len(self.shells))

        self.q_vectors = {}

        for q in self.shells:
            samples = spherical_vectors(q, self.width, self.n_samples, rng)
            lattice_hkl_vectors, _ = self.lattice_vectors_with_weights(
                samples,
                self._unit_cell,
            )
            q_vectors = self.hkl_to_qvectors(lattice_hkl_vectors, self._unit_cell)

            selection = self.vectors_within_limits(
                q_vectors,
                q_min=q - 0.5 * self.width,
                q_max=q + 0.5 * self.width,
            )

            if not np.any(selection):
                self.q_vectors[q] = None
                continue

            lattice_hkl_vectors = lattice_hkl_vectors.T[selection].T
            q_vectors = q_vectors.T[selection].T
            n_found = q_vectors.shape[1]

            selection = fpsampling(
                q_vectors.T,
                self.n_vectors,
                partial(spherical_vectors, q=1, q_width=0, n_vecs=1),
                rng,
            )
            lattice_hkl_vectors = lattice_hkl_vectors.T[selection].T
            q_vectors = q_vectors.T[selection].T

            if self.force_equal_weights:
                weights = np.ones(q_vectors.shape[1])
            else:
                samples = spherical_vectors(q, self.width, self.n_samples, rng)
                tree = KDTree(q_vectors.T)
                _, indices = tree.query(samples.T)
                weights = np.bincount(indices, minlength=q_vectors.shape[1])
                weights = q_vectors.shape[1] * weights / self.n_samples

            self.q_vectors[q] = {
                "q_vectors": q_vectors,
                "n_q_vectors": q_vectors.shape[1],
                "n_q_found": n_found,
                "weights": weights,
                "q": q,
                "hkls": lattice_hkl_vectors,
            }

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
