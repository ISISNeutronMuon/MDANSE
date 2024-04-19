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

import numpy as np


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Mathematics.LinearAlgebra import Vector


class VectorConfigurator(IConfigurator):
    """
    This configurator allows to input a 3D vector, by giving its 3 components
    """

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

        self._valueType = valueType

        self._normalize = normalize

        self._notNull = notNull

        self._dimension = dimension

    def configure(self, value):
        """
        Configure a vector.

        :param value: the vector components.
        :type value: sequence-like object
        """
        self._original_input = value

        if not isinstance(value, (list, tuple)):
            self.error_status = "Invalid input type"
            return

        if len(value) != self._dimension:
            self.error_status = "Invalid dimension"
            return

        vector = Vector(np.array(value, dtype=self._valueType))

        if self._normalize:
            vector = vector.normal()

        if self._notNull:
            if vector.length() == 0.0:
                self.error_status = "The vector is null"
                return

        self["vector"] = vector
        self["value"] = vector
        self.error_status = "OK"

    @property
    def valueType(self):
        """
        Returns the values type of the range.

        :return: the values type of the range.
        :rtype: one of int or float
        """

        return self._valueType

    @property
    def normalize(self):
        """
        Returns whether or not the configured vector will be normalized.

        :return: True if the vector has to be normalized, False otherwise.
        :rtype: bool
        """

        return self._normalize

    @property
    def notNull(self):
        """
        Returns whether or not a null vector is accepted.

        :return: True if a null vector is not accepted, False otherwise.
        :rtype: bool
        """

        return self._notNull

    @property
    def dimension(self):
        """
        Returns the dimension of the vector.

        :return: the dimension of the vector.
        :rtype: int
        """

        return self._dimension

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Value: %r\n" % self["value"]
