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

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell

if TYPE_CHECKING:
    from collections.abc import Callable

    from MDANSE.MolecularDynamics.UnitCell import UnitCell


def fpsampling(
    q_vectors: np.ndarray,
    n_vecs: int,
    random_vector_func: Callable[[], np.ndarray],
    rng: np.random.Generator,
) -> np.ndarray:
    """Basic farthest point sampling function used to sample q-vectors.
    Q-vectors are normalised to avoid sampling vectors from the ends of
    the shell. Distances between vectors are calculated on the angle
    between them.

    Parameters
    ----------
    q_vectors : np.ndarray
        Array of q_vectors.
    n_vecs : int
        Number of vectors to sample.
    random_vector_func : Callable[[], np.ndarray]
        A function which generates a single random vector.
    rng : np.random.Generator
        A numpy random number generator object.

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
        return rng.integers(low=0, high=n_points, size=1)
    elif n_points <= 0:
        raise ValueError("n_vecs should be greater than zero.")

    mag_q = np.linalg.norm(q_vectors, axis=1)
    if np.any(mag_q < 1e-9):
        # deal with the vector at the origin by turning into some
        # random unit vector
        random_vector = random_vector_func().T[0]
        zero_idx = np.where(mag_q < 1e-9)[0]
        q_vectors[zero_idx] = random_vector
        mag_q[zero_idx] = 1
    q_vectors = q_vectors / mag_q[:, None]

    dists = np.full(n_points, np.inf)
    selected = rng.integers(low=0, high=n_points)
    selection = np.zeros(n_vecs, dtype=int)
    selection[0] = selected

    for i in range(1, n_vecs):
        theta = np.arccos(np.clip(np.dot(q_vectors, q_vectors[selected]), -1.0, 1.0))
        dists = np.minimum(dists, theta)
        selected = np.argmax(dists)
        selection[i] = selected

    return selection


class LatticeQVectors(IQVectors):
    """Parent class for vector generators which need unit cell information."""

    is_lattice = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self._unit_cell is None:
            raise ValueError("The trajectory does not contain unit cell information.")
