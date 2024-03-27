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

import numpy as np

from MDANSE.Framework.QVectors.IQVectors import IQVectors, QVectorsError


class LatticeQVectors(IQVectors):
    is_lattice = True

    def __init__(self, chemical_system, status=None):
        super(LatticeQVectors, self).__init__(chemical_system, status)

        if self._chemical_system.configuration is None:
            raise QVectorsError("No configuration set for the chemical system")

        if not self._chemical_system.configuration.is_periodic:
            raise QVectorsError(
                "The universe must be periodic for building lattice-based Q vectors"
            )

        self._inverseUnitCell = (
            2.0 * np.pi * self._chemical_system.configuration.unit_cell.inverse
        )

        self._directUnitCell = (
            2.0 * np.pi * self._chemical_system.configuration.unit_cell.direct
        )
