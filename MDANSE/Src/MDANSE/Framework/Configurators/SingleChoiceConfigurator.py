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


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class SingleChoiceConfigurator(IConfigurator):
    """
    This Configurator allows to select a single item among multiple choices.
    """

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

        self._choices = choices if choices is not None else []

    def configure(self, value):
        """
        Configure the input item.

        :param value: the input selection list.
        :type value: list
        """
        self._original_input = value

        try:
            self["index"] = self._choices.index(value)
        except ValueError:
            self.error_status = f"{value} item is not a valid choice"
            return
        else:
            self["value"] = value
        self.error_status = "OK"

    @property
    def choices(self):
        """
        Returns the list of allowed selection items.

        :return: the list of allowed selection items.
        :rtype: list
        """

        return self._choices

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """
        if "value" not in self:
            return "Not configured yet\n"

        return "Selected item: %r\n" % self["value"]
