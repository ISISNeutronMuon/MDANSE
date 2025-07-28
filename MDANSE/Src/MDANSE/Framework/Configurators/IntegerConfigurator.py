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

from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
)


class IntegerConfigurator(IConfigurator):
    """Inputs a single integer number."""

    _default = 0

    def __init__(
        self, name, mini=None, maxi=None, choices=None, exclude=None, **kwargs
    ):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: int or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: int or None
        :param choices: the list of integers allowed for the input value. If None, any value will be allowed.
        :type choices: int-list or None
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self.mini = int(mini) if mini is not None else None

        self.maxi = int(maxi) if maxi is not None else None

        self.choices = choices if choices is not None else []

        self._exclude = exclude if exclude is not None else ()

    def configure(self, value):
        """
        Configure an integer value.

        :param value: the integer to be configured.
        :type value: int
        """
        if not self.update_needed(value):
            return

        self._original_input = value
        self["value"] = self._default

        try:
            value = int(value)
        except (TypeError, ValueError) as e:
            self.error_status = "Wrong input for an integer" + str(e)
            return

        if self.choices:
            if value not in self.choices:
                self.error_status = "the input value is not a valid choice."
                return

        if self.mini is not None:
            if value < self.mini:
                self.error_status = f"the input value is lower than {self.mini}"
                return

        if self.maxi is not None:
            if value > self.maxi:
                self.error_status = f"the input value is higher than {self.maxi}"
                return

        if self._exclude:
            if value in self._exclude:
                self.error_status = f"the input value is forbidden; forbidden values are {self._exclude}"
                return

        self["value"] = value
        self.error_status = "OK"
