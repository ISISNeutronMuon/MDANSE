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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import collections
import itertools
import operator

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class GridQVectors(LatticeQVectors):
    """ """

    settings = collections.OrderedDict()
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
        lrange = self._configuration["krange"]["value"]
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
        vects = np.dot(self._inverseUnitCell, hkls)

        dists = np.sqrt(np.sum(vects**2, axis=0))

        minDist = dists.min()
        maxDist = dists.max()

        bins = np.arange(minDist, maxDist + qstep / 2, qstep)
        inds = np.digitize(dists, bins) - 1

        dists = bins[inds]

        dists = zip(range(len(dists)), dists)
        dists.sort(key=operator.itemgetter(1))
        qGroups = itertools.groupby(dists, key=operator.itemgetter(1))
        qGroups = collections.OrderedDict(
            [(k, [item[0] for item in v]) for k, v in qGroups]
        )

        if self._status is not None:
            self._status.start(len(qGroups))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q, v in qGroups.items():
            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]["q"] = q
            self._configuration["q_vectors"][q]["q_vectors"] = vects[:, v]
            self._configuration["q_vectors"][q]["n_q_vectors"] = len(v)
            self._configuration["q_vectors"][q]["hkls"] = hkls[:, v]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
