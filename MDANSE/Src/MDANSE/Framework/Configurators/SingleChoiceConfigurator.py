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


class SingleChoiceConfigurator(IConfigurator):
    """Selects a single item from multiple choices."""

    _default = []

    def __init__(self, name, choices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        """

        IConfigurator.__init__(self, name, **kwargs)

        self.choices = choices if choices is not None else []

    def configure(self, value):
        """
        Configure the input item.

        :param value: the input selection list.
        :type value: list
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        try:
            self["index"] = self.choices.index(value)
        except ValueError:
            self.error_status = f"{value} item is not a valid choice"
            return
        else:
            self["value"] = value
        self.error_status = "OK"
