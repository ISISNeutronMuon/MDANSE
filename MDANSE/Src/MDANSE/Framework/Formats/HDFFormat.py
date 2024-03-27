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
import h5py
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.Framework.OutputVariables import IOutputVariable


class HDFFormat(IFormat):
    """
    This class handles the writing of output variables in HDF file format.

    Attributes
    ----------
    extension : str
        Extension used when writing.
    extensions : list[str]
        Other possible extension of this file format.
    """

    extension = ".h5"
    extensions = [".h5", ".hdf"]

    @classmethod
    def write(
        cls,
        filename: str,
        data: dict[str, IOutputVariable],
        header: str = "",
        extension: str = extensions[0],
    ) -> None:
        """Write a set of output variables into an HDF file.

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
        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename, extension)

        # The HDF output file is opened for writing.
        outputFile = h5py.File(filename, "w")

        if header:
            # This is to avoid any segmentation fault when writing the HDF header field
            header = str(header)

            outputFile.attrs["header"] = header

        # Loop over the OutputVariable instances to write.

        for var in list(data.values()):
            varName = str(var.varname).strip().replace("/", "|")

            dset = outputFile.create_dataset(varName, data=var, shape=var.shape)

            # All the attributes stored in the OutputVariable instance are written to the HDF file.
            for k, v in list(vars(var).items()):
                dset.attrs[k] = v

        # The HDF file is closed.
        outputFile.close()
