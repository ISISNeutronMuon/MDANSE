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


class MultipleChoicesConfigurator(IConfigurator):
    """Allows to select several items from multiple choices.

    :attention: all the selected items must belong to the allowed selection list.
    """

    _default = []

    def __init__(self, name, choices=None, nChoices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        :param nChoices: the maximum number of values that can be selected or None if there is no restriction on this number.
        :type nChoices: int or None
        """

        IConfigurator.__init__(self, name, **kwargs)

        self.choices = choices

        self.nChoices = nChoices

    def configure(self, value):
        """
        Configure the input selection list.

        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input selection list.
        :type value: list
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        if self.nChoices is not None:
            if len(value) != self.nChoices:
                self.error_status = "invalid number of choices."
                return

        indices = []
        try:
            indices = [self.choices.index(v) for v in value]
        except ValueError:
            self.error_status = (
                f"{', '.join(set(value) - set(self.choices))} are not valid choices"
            )
            return

        if not indices:
            self.error_status = "Empty choices selection."
            return

        self["indices"] = indices
        self["choices"] = [self.choices[i] for i in indices]
        self["value"] = self["choices"]
        self.error_status = "OK"
