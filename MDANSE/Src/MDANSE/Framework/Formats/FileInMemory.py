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

from typing import TYPE_CHECKING

import h5py

from MDANSE.Framework.Formats.IFormat import IFormat

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.IJob import IJob
    from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
from .HDFFormat import HDFFormat


class FileInMemory(IFormat):
    """Handles the writing of output to an in-memory HDF5 structure.

    Attributes
    ----------
    extension : str
        Extension used when writing.
    extensions : list[str]
        Other possible extension of this file format.

    """

    extension = ".mda"
    extensions = [".mda"]

    @classmethod
    def write(
        cls,
        filename: str,
        data: dict[str, IOutputVariable],
        header: str = "",
        run_instance: IJob = None,
        extension: str = extensions[0],
    ) -> h5py.File:
        """Write the MDA data structure to an in-memory HDF object.

        Parameters
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
        return HDFFormat.write(
            filename, data, header, run_instance, extension, in_memory=True
        )
