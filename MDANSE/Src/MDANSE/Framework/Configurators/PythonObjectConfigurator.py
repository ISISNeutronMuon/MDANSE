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

import ast


from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class PythonObjectConfigurator(IConfigurator):
    """
    This Configurator allows to input and evaluate basic python object.

    The python object supported are strings, numbers, tuples, lists, dicts, booleans and None type.

    :note: this configurator is based on a literal and safe evaluation of the input using ast standard library module.
    """

    _default = '""'

    def configure(self, value):
        """
        Configure a python object.

        :param value: the python object to be configured and evaluated.
        :type value: strings, numbers, tuples, lists, dicts, booleans or None type.
        """
        self._original_input = value

        try:
            value = ast.literal_eval(repr(value))
        except SyntaxError as e:
            self.error_status = f"python code SyntaxError: {e}"
            return

        self["value"] = value
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """
        if "value" not in self:
            return "Not configured yet\n"

        return "Python object: %r\n" % self["value"]
