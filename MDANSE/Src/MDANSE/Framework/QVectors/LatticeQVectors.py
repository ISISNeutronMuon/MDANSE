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
from ase.neighborlist import _calc_expansion

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class LatticeQVectors(IQVectors):
    """Parent class for vector generators which need unit cell information."""

    is_lattice = True

    def __init__(self, unit_cell: UnitCell | None, status=None):
        super().__init__(unit_cell, status)

        if unit_cell is None:
            raise ValueError("The trajectory does not contain unit cell information.")

    def get_reciprocal_lattice_hkl(self, cutoff):
        """Use _calc_expansion function to "determines the minimum supercell
        (parallelepiped) that contains a sphere of radius `2.0 * rcmax`" and
        then generated the reciprocal lattice points within a cutoff radius.

        Parameters
        ----------
        cutoff : float
            The cutoff to distance of the hkl vector to generate.

        Returns
        -------
        np.array
            Numpy array of reciprocal lattice vectors.
        """
        max_h, max_k, max_l = _calc_expansion(
            2 * np.pi * self._unit_cell.inverse, (True, True, True), cutoff / 2
        )

        h_range = np.arange(-max_h, max_h + 1)
        k_range = np.arange(-max_k, max_k + 1)
        l_range = np.arange(-max_l, max_l + 1)

        recip_lattice_points = np.array(
            [[h, k, ll] for h in h_range for k in k_range for ll in l_range]
        )

        return recip_lattice_points.T
