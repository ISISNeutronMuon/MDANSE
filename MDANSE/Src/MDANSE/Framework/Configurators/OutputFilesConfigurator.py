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

from pathlib import Path
from typing import Optional

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Formats.IFormat import IFormat


class OutputFilesConfigurator(IConfigurator):
    """Allows the user to choose the output file for writing.

    This configurator allows to define:

    - output directory and the base file name,
    - format(s) of the output file(s),
    - logging level of the analysis run.

    The list of output files is built by joining the given output directory, the
    base file name and the extensions corresponding to the input file formats.

    For analysis, MDANSE currently supports:

    1. MDAFormat - an HDF5 file written to the disk,
    2. TextFormat - a tar file containing a text file for each array,
    3. FileInMemory - an HDF5 data object NOT written to the disk.

    FileInMemory is not available when running from the GUI.
    """

    log_options = ("no logs", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")
    _default = (
        "OUTPUT_FILENAME",
        ["MDAFormat", "TextFormat", "FileInMemory"],
        "no logs",
    )
    _label = "Output filename and formats (filename, [format, ...])"

    def __init__(self, name: str, formats: Optional[list[str]] = None, **kwargs):
        """Initialise the values of the output file name parser.

        Parameters
        ----------
        name : str
            Name of this variable to be shown in the interface
        formats : list[str], optional
            Output formats allowed for this analysis type, by default None
        kwargs : dict[str, Any]
            remaining keyword arguments for the parent class

        """
        IConfigurator.__init__(self, name, **kwargs)

        self.formats = (
            formats if formats is not None else OutputFilesConfigurator._default[1]
        )
        self.forbidden_files = []

    def configure(self, value):
        """Configure a set of output files for an analysis.

        :param value: the output files specifications. Must be a 3-tuple whose 1st element \
        is the output directory, 2nd element the basename and 3rd element a list of file formats.
        :type value: 3-tuple
        """
        self._original_input = value

        root, formats, logs = value
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

        if not formats:
            self.error_status = "no output formats specified"
            return

        for fmt in formats:
            if fmt not in self.formats:
                self.error_status = (
                    f"the output file format {fmt} is not a valid output format"
                )
                return

            if fmt not in IFormat.indirect_subclasses():
                self.error_status = f"the output file format {fmt} is not registered as a valid file format."
                return

        self["root"] = root
        self["formats"] = formats
        self["files"] = [
            root if root.suffix == ext else root.with_suffix(root.suffix + ext)
            for ext in (IFormat.create(f).extension for f in formats)
        ]
        for file in self["files"]:
            if file.absolute() in self.forbidden_files:
                self.error_status = f"File {file} is either open or being written into. Please pick another name."
                return

        self["value"] = self["files"]
        self["log_level"] = logs
        self["write_logs"] = logs != "no logs"
        self.error_status = "OK"
