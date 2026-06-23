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

from MDANSE.Framework.Projectors.IProjector import IProjector, ProjectorError
from MDANSE.Mathematics.LinearAlgebra import Vector


@IProjector.register("PlanarProjector")
class PlanarProjector(IProjector):
    def set_axis(self, axis):
        try:
            self._axis = Vector(axis)
        except (TypeError, ValueError) as err:
            raise ProjectorError(
                "Wrong axis definition: must be a sequence of 3 floats"
            ) from err

        try:
            self._axis = self._axis.normal()
        except ZeroDivisionError as err:
            raise ProjectorError("The axis vector can not be the null vector") from err

        self._projectionMatrix = np.identity(3) - np.outer(self._axis, self._axis)

    def __call__(self, value):
        try:
            return np.dot(value, self._projectionMatrix.T)
        except (TypeError, ValueError) as err:
            raise ProjectorError("Invalid data to apply projection on") from err
