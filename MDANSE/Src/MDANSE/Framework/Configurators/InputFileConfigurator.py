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

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class InputFileConfigurator(IConfigurator):
    """Uses a file as input. Very general."""

    _default = ""

    def __init__(
        self,
        name,
        wildcard="All files (*)",
        instance: Trajectory | None = None,
        **kwargs,
    ):
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

        self._instance = instance

        self.wildcard = wildcard

    def configure(self, value):
        """
        Configure an input file.

        :param value: the input file.
        :type value: str
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        value = PLATFORM.get_path(value)

        if not value.exists():
            self.error_status = f"The file {value} does not exist"
            return

        self["value"] = value
        self["filename"] = value
        self.error_status = "OK"
