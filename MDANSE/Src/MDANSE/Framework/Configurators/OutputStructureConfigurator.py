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

from pathlib import Path

from ase.io.formats import ioformats

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class OutputStructureConfigurator(IConfigurator):
    """Defines the name of the output (average) structure file.

    Allows to define:

    - output directory and file name,
    - output structure file format (supported by ASE io module),
    - logging level of the analysis run.

    """

    log_options = ("no logs", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")
    _default = ("OUTPUT_FILENAME", "vasp", "no logs")
    _label = "Output filename and format (filename, format)"

    def __init__(self, name, formats=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param formats: the list of output file formats supported.
        :type formats: list of str
        """

        IConfigurator.__init__(self, name, **kwargs)

        self.formats = [fmt for fmt in ioformats if ioformats[fmt].can_write]
        self.forbidden_files = []

    def configure(self, value):
        """
        Configure a set of output files for an analysis.

        :param value: the output files specifications. Must be a 3-tuple whose 1st element \
        is the output directory, 2nd element the basename and 3rd element a list of file formats.
        :type value: 3-tuple
        """

        self._original_input = value

        root, format, logs = value
        root = Path(root)

        if logs not in self.log_options:
            self.error_status = "log level option not recognised"
            return

        if not root:
            self.error_status = "empty root name for the output file."
            return

        if not PLATFORM.is_file_writable(root):
            self.error_status = f"the file {root} is not writable"
            return

        if format not in self.formats:
            self.error_status = "Output format is not supported"
            return

        self["root"] = root
        self["format"] = format
        self["file"] = root
        if self["file"].absolute() in self.forbidden_files:
            self.error_status = f"File {self['file']} is either open or being written into. Please pick another name."
            return
        self["log_level"] = logs
        self["write_logs"] = logs != "no logs"
        self["value"] = self["file"]
        self.error_status = "OK"
