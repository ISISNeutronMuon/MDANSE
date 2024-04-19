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


class BooleanConfigurator(IConfigurator):
    """
    This Configurator allows to input a Boolean Value (True or False).

    The input value can be directly provided as a Python boolean or by the using the following (standard)
     representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
    """

    _default = False

    _shortCuts = {
        True: True,
        "true": True,
        "yes": True,
        "y": True,
        "1": True,
        1: True,
        False: False,
        "false": False,
        "no": False,
        "n": False,
        "0": False,
        0: False,
    }

    def configure(self, value):
        """
        Configure an input value.

        The value must be one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0.

        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input value
        :type value: one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
        """
        self._original_input = value

        if value not in self._shortCuts:
            self.error_status = "Input is not recognised as a true/false value"
        else:
            self.error_status = "OK"
            self["value"] = self._shortCuts[value]

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        return "Value: %r\n" % self["value"]
