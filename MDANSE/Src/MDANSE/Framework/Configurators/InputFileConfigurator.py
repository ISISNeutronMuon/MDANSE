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
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class InputFileConfigurator(IConfigurator):
    """
    This Configurator allows to set an input file.
    """

    _default = ""

    def __init__(self, name, wildcard="All files|*", **kwargs):
        """
        Initializes the configurator object.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self._wildcard = wildcard

    def configure(self, value):
        """
        Configure an input file.

        :param value: the input file.
        :type value: str
        """

        value = PLATFORM.get_path(value)

        if not os.path.exists(value):
            self.error_status = f"The file {value} does not exist"
            return

        self["value"] = value
        self["filename"] = value
        self.error_status = "OK"

    @property
    def wildcard(self):
        """
        Returns the wildcard used to filter the input file.

        :return: the wildcard used to filter the input file.
        :rtype: str
        """

        return self._wildcard

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        return "Input file: %r\n" % self["value"]
