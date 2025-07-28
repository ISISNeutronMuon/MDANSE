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

from ase.io.formats import all_formats

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.MLogging import LOG


class AseInputFileConfigurator(InputFileConfigurator):
    """Sets an input file for the ASE-based converters."""

    _default = ""
    _allowed_formats = ["guess"] + [str(x) for x in all_formats.keys()]

    def __init__(self, name, wildcard="All files (*)", **kwargs):
        """
        Initializes the configurator object.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        """

        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)

        self.wildcard = wildcard
        self["format"] = kwargs.get("format", None)
        self["value"] = ""

    def configure(self, values):
        """
        Configure an input file.

        :param value: the input file.
        :type value: str
        """
        if not self.update_needed(values):
            return

        self._original_input = values
        try:
            value, file_format = values
        except ValueError:
            value, file_format = values, None

        value = PLATFORM.get_path(value)

        if not value.exists():
            if self.optional:
                return
            LOG.error(f"FILE MISSING in {self.name}")
            self.error_status = f"The file {value} does not exist"
            return

        if file_format == "guess":
            file_format = None

        if file_format is not None and file_format not in self._allowed_formats:
            LOG.error(f"WRONG FORMAT in {self.name}")
            self.error_status = f"The ASE file format {file_format} is not supported"
            return

        self["value"] = value
        self["filename"] = value
        self["format"] = file_format
        self.error_status = "OK"
