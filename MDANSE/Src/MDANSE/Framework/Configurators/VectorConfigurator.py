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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.LinearAlgebra import Vector


class VectorConfigurator(IConfigurator):
    """Inputs a vector given as 3 floating point numbers."""

    _default = [1.0, 0.0, 0.0]

    def __init__(
        self, name, valueType=int, normalize=False, notNull=False, dimension=3, **kwargs
    ):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param valueType: the numeric type for the vector.
        :type valueType: int or float
        :param normalize: if True the vector will be normalized.
        :type normalize: bool
        :param notNull: if True, the vector must be non-null.
        :type notNull: bool
        :param dimension: the dimension of the vector.
        :type dimension: int
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self.valueType = valueType

        self.normalize = normalize

        self.notNull = notNull

        self.dimension = dimension

    def configure(self, value):
        """
        Configure a vector.

        :param value: the vector components.
        :type value: sequence-like object
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        if not isinstance(value, (list, tuple)):
            self.error_status = "Invalid input type"
            return

        if len(value) != self.dimension:
            self.error_status = "Invalid dimension"
            return

        vector = Vector(np.array(value, dtype=self.valueType))

        if self.normalize:
            vector = vector.normal()

        if self.notNull:
            if vector.length() == 0.0:
                self.error_status = "The vector is null"
                return

        self["vector"] = vector
        self["value"] = vector
        self.error_status = "OK"
