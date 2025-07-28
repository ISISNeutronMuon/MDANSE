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

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class MillerIndicesQVectors(LatticeQVectors):
    """Generates vectors on a grid.

    Vectors are generated from HKL values based on
    the definition of the unit cell.
    They are then grouped into shells based on
    their length.
    """

    settings = collections.OrderedDict()
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0, 5.0, 0.5),
        },
    )
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["h"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )
    settings["k"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )
    settings["l"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )

    def _generate(self):
        hSlice = slice(
            self._configuration["h"]["first"],
            self._configuration["h"]["last"] + 1,
            self._configuration["h"]["step"],
        )
        kSlice = slice(
            self._configuration["k"]["first"],
            self._configuration["k"]["last"] + 1,
            self._configuration["k"]["step"],
        )
        lSlice = slice(
            self._configuration["l"]["first"],
            self._configuration["l"]["last"] + 1,
            self._configuration["l"]["step"],
        )

        # The hkl matrix (3,n_hkls)
        hkls = np.mgrid[hSlice, kSlice, lSlice]
        hkls = hkls.reshape(3, int(round(hkls.size / 3)))

        # The k matrix (3,n_hkls)
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)

        dists2 = np.sum(vects**2, axis=0)

        halfWidth = self._configuration["width"]["value"] / 2

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q in self._configuration["shells"]["value"]:
            qmin = max(0, q - halfWidth)

            q2low = qmin * qmin
            q2up = (q + halfWidth) * (q + halfWidth)

            hits = np.where((dists2 >= q2low) & (dists2 <= q2up))[0]

            nHits = len(hits)

            if nHits != 0:
                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]["q_vectors"] = vects[:, hits]
                self._configuration["q_vectors"][q]["n_q_vectors"] = nHits
                self._configuration["q_vectors"][q]["q"] = q
                self._configuration["q_vectors"][q]["hkls"] = self.qvectors_to_hkl(
                    vects[:, hits], self._unit_cell
                )

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
