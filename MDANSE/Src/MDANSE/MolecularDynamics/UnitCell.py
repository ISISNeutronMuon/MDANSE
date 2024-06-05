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
import math
import itertools as it

import numpy as np
from numpy.typing import ArrayLike


class UnitCell:
    """
    This class stores a unit cell, which is stored row-wise i.e. the a, b and c vectors are
    respectively the first, second and third row of the unit cell matrix.
    """

    def __init__(self, unit_cell: ArrayLike) -> None:
        """
        The constructor.

        :param unit_cell: the unit cell matrix
        :type unit_cell: 3x3 numpy array
        """

        self._unit_cell = np.array(unit_cell).astype(np.float64)

        if self._unit_cell.shape != (3, 3):
            raise ValueError(
                f"the unit cell must have a shape of 3×3 but {self._unit_cell.shape} was provided."
            )

        self._inverse_unit_cell = np.linalg.pinv(self._unit_cell)

    def __eq__(self, other: "UnitCell") -> bool:
        if isinstance(other, UnitCell):
            return np.allclose(self._unit_cell, other._unit_cell)
        else:
            return False

    def __repr__(self) -> str:
        return f"MDANSE.MolecularDynamics.UnitCell.UnitCell({repr(self._unit_cell)})"

    @property
    def a_vector(self) -> np.ndarray:
        """
        Return the a vector.

        :return: the a vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[0, :]

    @property
    def b_vector(self) -> np.ndarray:
        """
        Return the b vector.

        :return: the b vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[1, :]

    @property
    def c_vector(self) -> np.ndarray:
        """Return the c vector.

        :return: the c vector
        :rtype: numpy.ndarray
        """
        return self._unit_cell[2, :]

    @property
    def direct(self) -> np.ndarray:
        """
        Return the unit cell matrix.

        :return: the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._unit_cell

    @property
    def inverse(self) -> np.ndarray:
        """
        Return the inverse of the unit cell matrix.

        :return: the inverse of the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._inverse_unit_cell

    @property
    def transposed_direct(self) -> np.ndarray:
        """
        Return the transposed of the unit cell matrix.

        :return: the transposed of the unit cell matrix
        :rtype: numpy.ndarray
        """
        return self._unit_cell.T

    @property
    def transposed_inverse(self) -> np.ndarray:
        """
        Return the transposed of the inverse of unit cell matrix.

        :return: the transposed of the inverse of the unit cell matrix
        :rtype: numpy.ndarray
        """

        return self._inverse_unit_cell.T

    @property
    def volume(self) -> float:
        """
        Return the volume unit cell matrix.

        :return: the volume of the unit cell
        :rtype: float
        """

        return np.abs(
            np.dot(
                np.cross(self._unit_cell[0, :], self._unit_cell[1, :]),
                self._unit_cell[2, :],
            )
        )

    @property
    def abc_and_angles(self):
        a, b, c = self.a_vector, self.b_vector, self.c_vector
        abc = [np.linalg.norm(vector) for vector in [a, b, c]]
        alpha = np.linalg.norm(np.cross(b, c)) / (abc[1] * abc[2])
        beta = np.linalg.norm(np.cross(c, a)) / (abc[2] * abc[0])
        gamma = np.linalg.norm(np.cross(a, b)) / (abc[0] * abc[1])
        angles = np.degrees(np.arcsin([alpha, beta, gamma]))
        return *abc, *angles


def get_expansions(direct, cutoff) -> tuple[int, int, int]:
    """Determine the expansions required to generate a supercell which
    can contain a sphere with a radius of the cutoff distance.

    Parameters
    ----------
    direct : numpy.ndarray
        The direct matrix of the unit cell.
    cutoff : float
        Max cutoff distance used to determine the expansions of the
        supercell.

    Returns
    -------
    tuple[int, int, int]
        A tuple of supercell expansions.
    """
    vec_a, vec_b, vec_c = direct
    a = np.linalg.norm(vec_a)
    b = np.linalg.norm(vec_b)
    c = np.linalg.norm(vec_c)

    i, j, k = reversed(np.argsort([a, b, c]))
    vecs = [vec_a, vec_b, vec_c]
    lens = [a, b, c]

    vec_i = vecs[i]
    vec_j = vecs[j]
    vec_k = vecs[k]

    # expand with the longest vector
    max_i = math.ceil(2 * cutoff / lens[i])

    # expand with the second-longest vector
    oproj = vec_j - vec_i * (vec_j @ vec_i) / (vec_i @ vec_i)
    max_j = math.ceil(2 * cutoff / np.linalg.norm(oproj))

    # expand with the smallest vector
    cross_ij = np.cross(vec_i, vec_j)
    proj = cross_ij * (vec_k @ cross_ij) / (cross_ij @ cross_ij)
    max_k = math.ceil(2 * cutoff / np.linalg.norm(proj))

    maxs = sorted(zip([max_i, max_j, max_k], [i, j, k]), key=lambda x: x[1])
    return maxs[0][0], maxs[1][0], maxs[2][0]


def create_supercell(rs, direct, inverse, mol_idxs, sym_idxs, cutoff):
    """Create a supercell which can contain a sphere with a radius of
    the cutoff distance.

    Parameters
    ----------
    rs : np.ndarray
        Unit cell coordinates.
    direct : np.ndarray
        The direct matrix of the unit cell.
    inverse : np.ndarray
        The inverse matrix of the unit cell.
    mol_idxs : np.ndarray
        Molecule indexes.
    sym_idxs : np.ndarray
        Atom symbol indexes.
    cutoff : float
        The cutoff distance.

    Returns
    -------
    tuple
        A tuple of the supercell coordinates, direct and inverse
        matrices, and the molecule and symbol indexes
    """
    max_u, max_v, max_w = get_expansions(direct, cutoff)

    us = np.arange(max_u)
    vs = np.arange(max_v)
    ws = np.arange(max_w)

    rs_frac = rs @ inverse.T
    sc_pos_frac = [rs_frac]
    for u, v, w in it.product(us, vs, ws):
        if (u, v, w) == (0, 0, 0):
            continue
        sc_pos_frac.append(np.array([u, v, w]) + rs_frac)
    sc_rs = np.vstack(sc_pos_frac) @ direct.T

    sc_direct = np.array([[max_u], [max_v], [max_w]]) * direct

    n_atms = len(mol_idxs)
    sc_mol_idxs = [mol_idxs]
    for i in range(max_u * max_v * max_w):
        if i == 0:
            continue
        sc_mol_idxs.append(mol_idxs + i * n_atms)
    sc_mol_idxs = np.hstack(sc_mol_idxs)

    sc_sym_idxs = np.tile(sym_idxs, max_u * max_v * max_w)

    return sc_rs, sc_direct, np.linalg.pinv(sc_direct), sc_mol_idxs, sc_sym_idxs
