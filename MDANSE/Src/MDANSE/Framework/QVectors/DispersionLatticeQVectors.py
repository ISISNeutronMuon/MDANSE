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

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class DispersionLatticeQVectors(LatticeQVectors):
    r"""Generates Q vectors along a line in the HKL units of the simulation box.

    The input 'start' and 'step' vectors are expressed as HKL values of the
    crystal lattice defined by the simulation box. Every vector will be
    generated as :math:`\mathbf{k}_{start} + n\mathbf{k}_{step}` for
    integer n from 0 to n_steps.
    """

    settings = {}
    settings["start"] = (
        "VectorConfigurator",
        {"valueType": int, "notNull": False, "default": [0, 0, 0]},
    )
    settings["step"] = (
        "VectorConfigurator",
        {"valueType": int, "notNull": True, "default": [1, 0, 0]},
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {"label": "number of steps", "mini": 1, "default": 10},
    )

    def _generate(self):
        start = self._configuration["start"]["value"].array
        step_vector = self._configuration["step"]["value"].array
        n_steps = self._configuration["n_steps"]["value"]

        hkls = np.array(start)[:, np.newaxis] + np.outer(
            step_vector,
            np.arange(0, n_steps),
        )
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)
        hkl_vectors, weights = self.lattice_vectors_with_weights(vects, self._unit_cell)
        # The k matrix (3,n_hkls)
        q_vectors = self.hkl_to_qvectors(hkl_vectors, self._unit_cell)

        dists = np.linalg.norm(q_vectors, axis=0)
        sign_array = np.sign(np.dot(step_vector, hkl_vectors))
        keyvals = dists.copy()
        keyvals[sign_array < 0] *= -1

        if self._status is not None:
            self._status.start(len(dists))

        self._configuration["q_vectors"] = {}

        for i, v in enumerate(keyvals):
            self._configuration["q_vectors"][v] = {
                "q_vectors": q_vectors[:, i][:, np.newaxis],
                "n_q_vectors": weights[i],
                "weights": weights[i : i + 1],
                "q": v,
                "hkls": hkl_vectors[:, i][:, np.newaxis],
            }
            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
