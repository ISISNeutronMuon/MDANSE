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


@IConfigurator.register("VectorConfigurator")
class VectorConfigurator(IConfigurator):
    """Inputs a vector given as 3 floating point numbers."""

    _default = [1.0, 0.0, 0.0]

    def __init__(
        self,
        name: str,
        valueType: type = int,
        normalize: bool = False,
        notNull: bool = False,
        dimension: int = 3,
        mini: int | float | None = None,
        maxi: int | float | None = None,
        **kwargs,
    ):
        """
        Initializes the configurator.

        Parameters
        ----------
        name : str
            The name of the configurator as it will appear in the configuration.
        valueType : type
            The numeric type for the vector, `int` or `float`.
        normalize : bool
            if True the vector will be normalized.
        notNull : bool
            If True, the vector must be non-null.
        dimension : int
            The dimension of the vector.
        mini : int or float or None
            The minimum value of the vectors values.
        maxi : int or float or None
            The maximum value of the vectors values.
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self.valueType = valueType

        self.normalize = normalize

        self.notNull = notNull

        self.dimension = dimension

        self.mini = mini

        self.maxi = maxi

    def configure(self, value: list | tuple):  # noqa: PLR0911
        """
        Configure a vector.

        Parameters
        ----------
        value : list or tuple
            The vector components.
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        if not isinstance(value, list | tuple):
            self.error_status = "Invalid input type should be list or tuple."
            return

        if self.valueType is int and any(i % 1 != 0 for i in value):
            self.error_status = "Input values are not integer valued."
            return

        if len(value) != self.dimension:
            self.error_status = f"This vector should have {self.dimension} components."
            return

        if self.mini is not None and any(i < self.mini for i in value):
            self.error_status = (
                f"Value in vector smaller than the minimum value of {self.mini}."
            )
            return

        if self.maxi is not None and any(i > self.maxi for i in value):
            self.error_status = (
                f"Value in vector larger than the maximum value of {self.maxi}."
            )
            return

        vector = Vector(np.array(value, dtype=self.valueType))

        if self.normalize:
            vector = vector.normal()

        if self.notNull and vector.length() == 0.0:
            self.error_status = "The vector is null."
            return

        self["vector"] = vector
        self["value"] = vector
        self.error_status = "OK"
