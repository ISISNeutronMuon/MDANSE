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

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class OutputDirectoryConfigurator(IConfigurator):
    """
    This Configurator allows to set an output directory.
    """

    _default = os.getcwd()

    def __init__(self, name, new=False, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param new: if True the output directory path will be checked for being new.
        :type new: bool
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._new = new

    def configure(self, value):
        """
        Configure an output directory.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the output directory.
        :type value: str
        """
        self._original_input = value

        value = PLATFORM.get_path(value)

        if self._new:
            if os.path.exists(value):
                self.error_status = "the output directory must not exist"
                return

        self["value"] = value
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Output directory: %r\n" % self["value"]
