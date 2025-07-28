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

from operator import itemgetter

import numpy as np
from more_itertools import map_reduce

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class GridQVectors(LatticeQVectors):
    """Generates vectors on a grid.

    Vectors are generated from HKL values based on
    the definition of the unit cell.

    No symmetry considerations are used when generating
    the vectors.
    """

    settings = {}
    settings["hrange"] = (
        "RangeConfigurator",
        {"valueType": int, "includeLast": True, "default": (0, 8, 1)},
    )
    settings["krange"] = (
        "RangeConfigurator",
        {"valueType": int, "includeLast": True, "default": (0, 8, 1)},
    )
    settings["lrange"] = (
        "RangeConfigurator",
        {"valueType": int, "includeLast": True, "default": (0, 8, 1)},
    )
    settings["qstep"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 0.01})

    def _generate(self):
        hrange = self._configuration["hrange"]["value"]
        krange = self._configuration["krange"]["value"]
        lrange = self._configuration["lrange"]["value"]
        qstep = self._configuration["qstep"]["value"]

        nh = self._configuration["hrange"]["number"]
        nk = self._configuration["krange"]["number"]
        nl = self._configuration["lrange"]["number"]

        hkls = np.mgrid[
            hrange[0] : hrange[-1] + 1,
            krange[0] : krange[-1] + 1,
            lrange[0] : lrange[-1] + 1,
        ]
        hkls = hkls.reshape(3, nh * nk * nl)

        # The k matrix (3,n_hkls)
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)

        dists = np.sqrt(np.sum(vects**2, axis=0))

        minDist = dists.min()
        maxDist = dists.max()

        bins = np.arange(minDist, maxDist + qstep / 2, qstep)
        inds = np.digitize(dists, bins) - 1

        dists = enumerate(bins[inds])
        q_groups = map_reduce(dists, itemgetter(1), itemgetter(0))
        # Functions rely on ordered dicts for some reason?
        q_groups = {key: q_groups[key] for key in sorted(q_groups)}

        if self._status is not None:
            self._status.start(len(q_groups))

        self._configuration["q_vectors"] = {}

        for q, v in q_groups.items():
            self._configuration["q_vectors"][q] = {
                "q": q,
                "q_vectors": vects[:, v],
                "n_q_vectors": len(v),
                "hkls": hkls[:, v],
            }

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
