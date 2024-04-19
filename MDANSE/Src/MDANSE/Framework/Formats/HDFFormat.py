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
from typing import TYPE_CHECKING, Dict
from importlib import metadata

import h5py

from MDANSE.Framework.Formats.IFormat import IFormat

if TYPE_CHECKING:
    from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
    from MDANSE.Framework.Jobs.IJob import IJob


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
        data: Dict[str, "IOutputVariable"],
        header: str = "",
        run_instance: "IJob" = None,
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
        string_dt = h5py.special_dtype(vlen=str)

        filename = os.path.splitext(filename)[0]

        filename = "%s%s" % (filename, extension)

        # The HDF output file is opened for writing.
        outputFile = h5py.File(filename, "w")

        if header:
            # This is to avoid any segmentation fault when writing the HDF header field
            header = str(header)

            outputFile.attrs["header"] = header

        meta = outputFile.create_group("metadata")
        if run_instance is not None:
            meta.create_dataset(
                "task_name", data=str(run_instance.__class__.__name__), dtype=string_dt
            )
            meta.create_dataset(
                "MDANSE_version", data=str(metadata.version("MDANSE")), dtype=string_dt
            )

            inputs = run_instance.output_configuration()

            if inputs is not None:
                print(inputs)
                dgroup = meta.create_group("inputs")
                for key, value in inputs.items():
                    dgroup.create_dataset(key, data=value, dtype=string_dt)

        # Loop over the OutputVariable instances to write.

        for var in list(data.values()):
            varName = str(var.varname).strip().replace("/", "|")

            dset = outputFile.create_dataset(varName, data=var, shape=var.shape)

            # All the attributes stored in the OutputVariable instance are written to the HDF file.
            for k, v in list(vars(var).items()):
                dset.attrs[k] = v

        # The HDF file is closed.
        outputFile.close()
