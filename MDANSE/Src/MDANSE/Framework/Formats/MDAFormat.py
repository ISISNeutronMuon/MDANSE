from MDANSE.Framework.Formats.IFormat import IFormat

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
from .HDFFormat import HDFFormat


class MDAFormat(IFormat):
    """
    This class handles the writing of output variables in MDA file format.

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
        data: dict[str, "IOutputVariable"],
        header: str = "",
        extension: str = extensions[0],
    ) -> None:
        """Write a set of output variables into an HDF file with the
        MDANSE analysis file extension.

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
