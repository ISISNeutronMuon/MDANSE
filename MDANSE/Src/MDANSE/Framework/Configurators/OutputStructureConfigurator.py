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

from ase.io.formats import ioformats

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class OutputStructureConfigurator(IConfigurator):
    """
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from an analysis.

    Once configured, this configurator will provide a list of files built by joining the given output directory, the
    basename and the extensions corresponding to the input file formats.

    For analysis, MDANSE currently supports only the HDF and Text formats. To define a new output file format
    for an analysis, you must inherit from MDANSE.Framework.Formats.IFormat.IFormat interface.
    """

    _default = ("OUTPUT_FILENAME", "vasp")
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

        self._formats = [fmt for fmt in ioformats if ioformats[fmt].can_write]

    def configure(self, value):
        """
        Configure a set of output files for an analysis.

        :param value: the output files specifications. Must be a 3-tuple whose 1st element \
        is the output directory, 2nd element the basename and 3rd element a list of file formats.
        :type value: 3-tuple
        """
        self._original_input = value

        root, format, logs = value

        if not root:
            self.error_status = "empty root name for the output file."
            return

        dirname = os.path.dirname(root)

        try:
            PLATFORM.create_directory(dirname)
        except:
            self.error_status = f"the directory {dirname} is not writable"
            return

        if not format in self.formats:
            self.error_status = f"Output format is not supported"
            return

        self["root"] = root
        self["format"] = format
        self["file"] = root
        self["write_logs"] = logs
        self["value"] = self["file"]
        self.error_status = "OK"

    @property
    def formats(self):
        """
        Returns the list of output file formats supported.

        :return: the list of file formats supported.
        :rtype: list of str
        """
        return self._formats

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """
        if not "file" in self:
            return "Output File have not been defined"

        info = f"Output file: {self['file']}\n"

        return info

    @property
    def default(self) -> tuple[str, str]:
        """

        Returns
        -------
        tuple[str, str]
            A tuple of the default filename and format.
        """
        return self._default[0], self._default[1]
