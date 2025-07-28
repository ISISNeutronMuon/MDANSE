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


class DispersionLatticeQVectors(LatticeQVectors):
    """Generates Q vectors along a direction."""

    settings = collections.OrderedDict()
    settings["start"] = (
        "VectorConfigurator",
        {"valueType": int, "notNull": False, "default": [0, 0, 0]},
    )
    settings["direction"] = (
        "VectorConfigurator",
        {"valueType": int, "notNull": True, "default": [1, 0, 0]},
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {"label": "number of steps", "mini": 1, "default": 10},
    )

    def _generate(self):
        start = self._configuration["start"]["value"]
        direction = self._configuration["direction"]["value"]
        n_steps = self._configuration["n_steps"]["value"]

        hkls = np.array(start)[:, np.newaxis] + np.outer(
            direction, np.arange(0, n_steps)
        )

        # The k matrix (3,n_hkls)
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)

        dists = np.sqrt(np.sum(vects**2, axis=0))

        if self._status is not None:
            self._status.start(len(dists))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for i, v in enumerate(dists):
            self._configuration["q_vectors"][v] = {}
            self._configuration["q_vectors"][v]["q_vectors"] = vects[:, i][
                :, np.newaxis
            ]
            self._configuration["q_vectors"][v]["n_q_vectors"] = 1
            self._configuration["q_vectors"][v]["q"] = v
            self._configuration["q_vectors"][v]["hkls"] = hkls[:, i][:, np.newaxis]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
