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

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class LatticeQVectors(IQVectors):
    """Parent class for vector generators which need unit cell information."""

    is_lattice = True

    def __init__(self, unit_cell: UnitCell | None, status=None):
        super().__init__(unit_cell, status)

        if unit_cell is None:
            raise ValueError("The trajectory does not contain unit cell information.")
