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
import itertools
import operator

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class ApproximateDispersionQVectors(LatticeQVectors):
    """Generates Q vectors along a path between two points."""

    settings = collections.OrderedDict()
    settings["q_start"] = (
        "VectorConfigurator",
        {
            "label": "Q start (nm^-1)",
            "valueType": float,
            "notNull": False,
            "default": [0, 0, 0],
        },
    )
    settings["q_end"] = (
        "VectorConfigurator",
        {
            "label": "Q end (nm^-1)",
            "valueType": float,
            "notNull": False,
            "default": [1, 0, 0],
        },
    )
    settings["q_step"] = (
        "FloatConfigurator",
        {"label": "Q step (nm^-1)", "mini": 1.0e-6, "default": 0.1},
    )

    def _generate(self):
        qStart = self._configuration["q_start"]["value"]
        qEnd = self._configuration["q_end"]["value"]
        qStep = self._configuration["q_step"]["value"]

        d = (qEnd - qStart).length()
        try:
            n = (qEnd - qStart).normal()
        except ZeroDivisionError:
            self._configuration[
                "q_end"
            ].error_status = "Zero-length vector cannot be used here"
            return
        nSteps = int(d / qStep) + 1

        vects = (
            np.array(qStart)[:, np.newaxis] + np.outer(n, np.arange(0, nSteps)) * qStep
        )

        hkls = self.qvectors_to_hkl(vects, self._unit_cell)

        dists = np.sqrt(np.sum(vects**2, axis=0))
        dists = list(zip(range(len(dists)), dists))
        dists.sort(key=operator.itemgetter(1))
        qGroups = itertools.groupby(dists, key=operator.itemgetter(1))
        qGroups = collections.OrderedDict(
            [(k, [item[0] for item in v]) for k, v in qGroups]
        )

        if self._status is not None:
            self._status.start(len(qGroups))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for k, v in qGroups.items():
            self._configuration["q_vectors"][k] = {}
            self._configuration["q_vectors"][k]["q"] = k
            self._configuration["q_vectors"][k]["q_vectors"] = vects[:, v]
            self._configuration["q_vectors"][k]["n_q_vectors"] = len(v)
            self._configuration["q_vectors"][k]["hkls"] = hkls[:, v]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
