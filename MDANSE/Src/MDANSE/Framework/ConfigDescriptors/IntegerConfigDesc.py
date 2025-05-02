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
from typing import Optional, SupportsInt, Set

from .AbsConfigDesc import ConfigError, ConfigureDescriptor


class IntegerConfigDesc(ConfigureDescriptor[int]):
    """Configurator takes an integer input."""

    _old_name = "IntegerConfigurator"

    def __init__(self,
                 minimum: Optional[int] = None,
                 maximum: Optional[int] = None,
                 **params):
        super().__init__(mini=minimum, maxi=maximum, **params)
        self.minimum = minimum
        self.maximum = maximum

    @property
    def minimum(self) -> Optional[int]:
        """
        Returns the minimum value allowed for an input integer.

        :return: the minimum value allowed for an input value integer.
        :rtype: int or None
        """
        return self._minimum

    @minimum.setter
    def minimum(self, value: Optional[SupportsInt]):
        if value is None:
            self._minimum = None
        self._minimum = int(value)

    @property
    def maximum(self) -> Optional[int]:
        """
        Returns the maximum value allowed for an input integer.

        :return: the maximum value allowed for an input value integer.
        :rtype: int or None
        """
        return self._minimum

    @maximum.setter
    def maximum(self, value: Optional[SupportsInt]):
        if value is None:
            self._maximum = None
        self._maximum = int(value)

    def validate(self, value: SupportsInt, *_) -> int:
        try:
            value = int(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid integer.") from error

        super().validate(value)

        if self.minimum > value > self.maximum:
            raise ConfigError(f"Value ({value}) outside of valid range ({self.minimum}, {self.maximum})")

        return value
