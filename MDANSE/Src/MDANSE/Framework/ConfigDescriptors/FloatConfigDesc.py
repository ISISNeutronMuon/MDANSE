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
from collections.abc import Container
from typing import Optional, Set, SupportsFloat
from math import isclose

from .AbsConfigDesc import ConfigError, ConfigureDescriptor


class FloatConfigDesc(ConfigureDescriptor[float]):
    """
    This configurator allows to input a float value.
    """

    _old_name = "FloatConfigurator"

    def __init__(self,
                 minimum: Optional[float] = None,
                 maximum: Optional[float] = None,
                 non_zero: float = 0.,
                 **params):
        super().__init__(**params)
        self.minimum = minimum
        self.maximum = maximum
        self.non_zero = 0.

    @property
    def minimum(self) -> Optional[float]:
        """
        Returns the minimum value allowed for an input float.

        :return: the minimum value allowed for an input value float.
        :rtype: int or None
        """
        return self._minimum

    @minimum.setter
    def minimum(self, value: Optional[SupportsFloat]):
        if value is None:
            self._minimum = None
        self._minimum = float(value)

    @property
    def maximum(self) -> Optional[int]:
        """
        Returns the maximum value allowed for an input float.

        :return: the maximum value allowed for an input value float.
        :rtype: int or None
        """
        return self._minimum

    @maximum.setter
    def maximum(self, value: Optional[SupportsFloat]):
        if value is None:
            self._maximum = None
        self._maximum = float(value)

    def validate(self, value: SupportsFloat, *_) -> float:
        try:
            value = float(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid float.") from error

        super().validate(value)

        if self.minimum > value > self.maximum:
            raise ConfigError(f"Value ({value}) outside of valid range ({self.minimum}, {self.maximum})")

        if self.non_zero and isclose(value, 0., self.non_zero):
            raise ConfigError(f"Non-null val ({value}) is too close to zero.")


        return value
