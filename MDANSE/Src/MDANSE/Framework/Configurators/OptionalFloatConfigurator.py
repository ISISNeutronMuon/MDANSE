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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class OptionalFloatConfigurator(IConfigurator):
    """Inputs a single floating point number. Empty input is allowed."""

    _default = [False, 1.0]

    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: float or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: float or None
        :param choices: the list of floats allowed for the input value. If None, any value will be allowed.
        :type choices: list of float or None
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self.mini = float(mini) if mini is not None else None

        self.maxi = float(maxi) if maxi is not None else None

        self.choices = choices if choices is not None else []

        self.label_text = kwargs.pop("label_text", "Apply")

    def configure(self, value):
        """
        Configure an input value.

        :param value: the input value
        :type value: float
        """
        if not self.update_needed(value):
            return

        self["value"] = self._default[1]
        self["use_it"] = False
        self._original_input = value
        if not value[0]:
            self.error_status = "OK"
            return

        try:
            value[1] = float(value[1])
        except (TypeError, ValueError):
            self.error_status = f"Wrong value {value[1]} in {self}"
            return

        if self.choices:
            if value[1] not in self.choices:
                self.error_status = "the input value is not a valid choice."
                return

        if self.mini is not None:
            if value[1] < self.mini:
                self.error_status = f"the input value is lower than {self.mini}"
                return

        if self.maxi is not None:
            if value[1] > self.maxi:
                self.error_status = f"the input value is higher than {self.maxi}"
                return

        self.error_status = "OK"
        self["value"] = value[1]
        self["use_it"] = True
