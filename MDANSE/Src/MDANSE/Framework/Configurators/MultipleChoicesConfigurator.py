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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class MultipleChoicesConfigurator(IConfigurator):
    """
    This Configurator allows to select several items among multiple choices.

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

        self._choices = choices

        self._nChoices = nChoices

    def configure(self, value):
        """
        Configure the input selection list.

        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input selection list.
        :type value: list
        """

        if self._nChoices is not None:
            if len(value) != self._nChoices:
                self.error_status = f"invalid number of choices."
                return

        indexes = []
        for v in value:
            try:
                indexes.append(self._choices.index(v))
            except ValueError:
                self.error_status = f"{v} item is not a valid choice"
                return

        if not indexes:
            self.error_status = "Empty choices selection."
            return

        self["indexes"] = indexes
        self["choices"] = [self._choices[i] for i in indexes]
        self["value"] = self["choices"]
        self.error_status = "OK"

    @property
    def choices(self):
        """
        Returns the list of allowed selection items.

        :return: the list of allowed selection items.
        :rtype: list
        """

        return self._choices

    @property
    def nChoices(self):
        """
        Returns the maximum number items that can be selected or None if there is no restriction on this number.

        :return: the maximum number items that can be selected.
        :rtype: int or None
        """

        return self._nChoices

    def get_information(self):
        return "Selected items: %r\n" % self["choices"]
