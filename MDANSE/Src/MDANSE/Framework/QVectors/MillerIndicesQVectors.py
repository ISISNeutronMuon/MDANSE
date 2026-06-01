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
from more_itertools import numeric_range

from MDANSE.Framework.Parameters import Float, Range
from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class MillerIndicesQVectors(LatticeQVectors):
    """Generates vectors on a grid.

    Vectors are generated from HKL values based on
    the definition of the unit cell.
    They are then grouped into shells based on
    their length.
    """

    shells = Range[float](include_last=True, minimum=0.0, default=(0.0, 5.0, 0.5))
    width = Float(minimum=1e-6, default=1.0)
    hrange = Range[int](include_last=True, default=(0, 8, 1), dtype=int)
    krange = Range[int](include_last=True, default=(0, 8, 1), dtype=int)
    lrange = Range[int](include_last=True, default=(0, 8, 1), dtype=int)

    def _generate(self):
        hSlice = slice(
            self.hrange.start,
            self.hrange.stop + 1,
            self.hrange.step,
        )
        kSlice = slice(
            self.krange.start,
            self.krange.stop + 1,
            self.krange.step,
        )
        lSlice = slice(
            self.lrange.start,
            self.lrange.stop + 1,
            self.lrange.step,
        )

        # The hkl matrix (3,n_hkls)
        hkls = np.mgrid[hSlice, kSlice, lSlice]
        hkls = hkls.reshape(3, round(hkls.size / 3))

        # The k matrix (3,n_hkls)
        vects = self.hkl_to_qvectors(hkls, self._unit_cell)

        dists2 = np.sum(vects**2, axis=0)

        halfWidth = self.width / 2

        if self._status is not None:
            self._status.start(len(self.shells))

        self.q_vectors = {}

        for q in self.shells:
            qmin = max(0, q - halfWidth)

            q2low = qmin * qmin
            q2up = (q + halfWidth) * (q + halfWidth)

            hits = np.where((dists2 >= q2low) & (dists2 <= q2up))[0]

            nHits = len(hits)

            if nHits != 0:
                self.q_vectors[q] = {
                    "q_vectors": vects[:, hits],
                    "n_q_vectors": nHits,
                    "n_q_found": nHits,
                    "weights": np.ones(nHits),
                    "q": q,
                    "hkls": self.qvectors_to_hkl(vects[:, hits], self._unit_cell),
                }
            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
