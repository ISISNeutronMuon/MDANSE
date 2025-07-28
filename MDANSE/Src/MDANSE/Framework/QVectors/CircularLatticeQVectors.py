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

import collections
import random

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors
from MDANSE.Mathematics.LinearAlgebra import Vector


class CircularLatticeQVectors(LatticeQVectors):
    """Generates Q vectors on a plane.

    Vectors are grouped into annuli (called 'shells')
    based on their length.

    Only vectors commensurate with the reciprocal
    space lattice vectors will be generated.
    |Q| values for which no valid vectors can
    be found are omitted in the output.
    """

    settings = collections.OrderedDict()
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
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["axis_1"] = (
        "VectorConfigurator",
        {"normalize": False, "notNull": True, "valueType": int, "default": [1, 0, 0]},
    )
    settings["axis_2"] = (
        "VectorConfigurator",
        {"normalize": False, "notNull": True, "valueType": int, "default": [0, 1, 0]},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        hkls = np.transpose(
            [
                self._configuration["axis_1"]["vector"],
                self._configuration["axis_2"]["vector"],
            ]
        )

        qVects = self.hkl_to_qvectors(hkls, self._unit_cell)

        qMax = (
            self._configuration["shells"]["last"]
            + 0.5 * self._configuration["width"]["value"]
        )

        uvMax = np.ceil([qMax / Vector(v).length() for v in qVects.T]) + 1
        # Enforce integers in uvMax
        uvMax = uvMax.astype(np.int64)

        idxs = np.mgrid[-uvMax[0] : uvMax[0] + 1, -uvMax[1] : uvMax[1] + 1]

        idxs = idxs.reshape(2, (2 * uvMax[0] + 1) * (2 * uvMax[1] + 1))

        vects = np.dot(qVects, idxs)

        dists2 = np.sum(vects**2, axis=0)

        halfWidth = self._configuration["width"]["value"] / 2

        nVectors = self._configuration["n_vectors"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q in self._configuration["shells"]["value"]:
            qmin = max(0, q - halfWidth)

            q2low = qmin * qmin
            q2up = (q + halfWidth) * (q + halfWidth)

            hits = np.where((dists2 >= q2low) & (dists2 <= q2up))[0]

            nHits = len(hits)

            if nHits != 0:
                n = min(nHits, nVectors)

                if nHits > nVectors:
                    hits = random.sample(hits, nVectors)

                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]["q_vectors"] = vects[:, hits]
                self._configuration["q_vectors"][q]["n_q_vectors"] = n
                self._configuration["q_vectors"][q]["q"] = q
                self._configuration["q_vectors"][q]["hkls"] = self.qvectors_to_hkl(
                    vects[:, hits], self._unit_cell
                )

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
