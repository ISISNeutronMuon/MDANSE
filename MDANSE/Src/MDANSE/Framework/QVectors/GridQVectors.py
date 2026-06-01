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

from MDANSE.Framework.Parameters import Float, Range
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class GridQVectors(LatticeQVectors):
    """Generates vectors on a grid.

    Vectors are generated from HKL values based on the definition of the unit cell.

    As opposed to MillerIndicesQVectors, this generator will use ALL the vectors
    in the specified range, assigning each one of them to one of the shells.

    The qstep parameter defines the size of the bin used for grouping vectors
    into shells based on their length.
    """

    hrange = Range[int](include_last=True, default=range(0, 8, 1), dtype=int)
    krange = Range[int](include_last=True, default=range(0, 8, 1), dtype=int)
    lrange = Range[int](include_last=True, default=range(0, 8, 1), dtype=int)
    qstep = Float(minimum=1e-6, default=0.01)

    def _get_grid(self):
        nh = len(self.hrange)
        nk = len(self.krange)
        nl = len(self.lrange)

        return np.mgrid[
            self.hrange[0] : self.hrange[-1] + 1,
            self.krange[0] : self.krange[-1] + 1,
            self.lrange[0] : self.lrange[-1] + 1,
        ].reshape(3, nh * nk * nl)

    def _get_qgroups(self):
        hkls = self._get_grid()

        # The k matrix (3,n_hkls)
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)

        dists = np.sqrt(np.sum(vects**2, axis=0))

        minDist = dists.min()
        maxDist = dists.max()

        bins = np.arange(minDist, maxDist + self.qstep / 2, self.qstep)
        inds = np.digitize(dists, bins) - 1

        dists = enumerate(bins[inds])

        q_groups = map_reduce(dists, itemgetter(1), itemgetter(0))
        return hkls, vects, {key: q_groups[key] for key in sorted(q_groups)}

    def _generate(self):
        hkls, vects, q_groups = self._get_qgroups()
        # Functions rely on ordered dicts for some reason?
        self.q_groups = {key: q_groups[key] for key in sorted(q_groups)}

        if self._status is not None:
            self._status.start(len(self.q_groups))

        self.q_vectors = {}

        for q, v in self.q_groups.items():
            self.q_vectors[q] = {
                "q": q,
                "q_vectors": vects[:, v],
                "n_q_vectors": len(v),
                "n_q_found": len(v),
                "weights": np.ones_like(v),
                "hkls": hkls[:, v],
            }

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()

    @property
    def shells(self):
        return sorted(self.q_vectors)
