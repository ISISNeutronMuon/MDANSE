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

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell


def fpsampling(q_vectors: np.ndarray, n_vecs: int) -> np.ndarray:
    """Basic farthest point sampling function used to sample q-vectors.

    Parameters
    ----------
    q_vectors : np.ndarray
        Array of q_vectors.
    n_vecs : int
        Number of vectors to sample.

    Returns
    -------
    np.ndarray
        Index of selected q-vectors.

    Raises
    ------
    ValueError
        When `n_vecs` is zero or less than zero.
    """
    n_points = q_vectors.shape[0]
    if n_vecs >= n_points:
        return np.arange(n_points)
    elif n_points == 1:
        return np.array([np.random.randint(0, n_points)])
    elif n_points <= 0:
        raise ValueError("n_vecs should be greater than zero.")

    dists = np.full(n_points, np.inf)
    selected = np.random.randint(n_points)
    selection = np.zeros(n_vecs, dtype=int)
    selection[0] = selected

    for i in range(1, n_vecs):
        diff = q_vectors - q_vectors[selected]
        dist_sq = np.sum(diff**2, axis=1)
        dists = np.minimum(dists, dist_sq)
        selected = np.argmax(dists)
        selection[i] = selected

    return selection


class LatticeQVectors(IQVectors):
    """Parent class for vector generators which need unit cell information."""

    is_lattice = True

    def __init__(self, unit_cell: UnitCell | None, status=None):
        super().__init__(unit_cell, status)

        if unit_cell is None:
            raise ValueError("The trajectory does not contain unit cell information.")
