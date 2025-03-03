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
                 choices: Container[int] = None,
                 exclude: Container[int] = None,
                 **params):
        super().__init__(mini=minimum, maxi=maximum, choices=choices, exclude=exclude, **params)
        self.minimum = minimum
        self.maximum = maximum
        self.choices = choices
        self.exclude = exclude

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

    @property
    def choices(self) -> Set[int]:
        """
        Returns the list of integers allowed for an input float.
        """
        return self._choices

    @choices.setter
    def choices(self, value: Container[int]):
        if value is None:
            self._choices = []
        self._choices = set(value)

    @property
    def exclude(self) -> Set[int]:
        """
        Returns the set of values which are not forbidden.

        Returns
        -------
        Set[int]
            Forbidden values.
        """
        return self._exclude

    @exclude.setter
    def exclude(self, value: Container[int]):
        if value is None:
            self._exclude = []
        self._exclude = set(value)

    def validate(self, value: SupportsInt) -> int:
        try:
            value = int(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid integer.") from error

        if value not in self.choices:
            raise ConfigError(f"Value ({value}) not in choices ({self.choices!r}).")

        if self.minimum > value > self.maximum:
            raise ConfigError(f"Value ({value}) outside of valid range ({self.minimum}, {self.maximum})")

        if value in self.exclude:
            raise ConfigError(f"Value ({value}) in exluded values ({self.exclude!r})")

        return value
