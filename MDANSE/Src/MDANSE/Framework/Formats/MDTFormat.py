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

from typing import TYPE_CHECKING, Dict

from MDANSE.Framework.Formats.IFormat import IFormat

if TYPE_CHECKING:
    from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
from .HDFFormat import HDFFormat


class MDTFormat(IFormat):
    """
    This class handles the writing of output variables in MDT file format.

    Attributes
    ----------
    extension : str
        Extension used when writing.
    extensions : list[str]
        Other possible extension of this file format.
    """

    extension = ".mdt"
    extensions = [".mdt"]

    @classmethod
    def write(
        cls,
        filename: str,
        data: Dict[str, "IOutputVariable"],
        header: str = "",
        inputs: Dict[str, str] = None,
        extension: str = extensions[0],
    ) -> None:
        """Write a set of output variables into an HDF file with the
        MDANSE trajectory file extension.

        Attributes
        ----------
        filename : str
            The path to the output HDF file.
        data : dict[str, IOutputVariable]
            The data to be written out
        header : str
            The header to add to the output file.
        extension : str
            The extension of the file.
        """
        HDFFormat.write(filename, data, header, extension)
