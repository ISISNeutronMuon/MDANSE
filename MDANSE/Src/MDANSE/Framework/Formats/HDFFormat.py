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

import json
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

import h5py

from MDANSE import PLATFORM
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.IJob import IJob
    from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable


json_decoder = json.decoder.JSONDecoder()


def check_metadata(hdf5_file: h5py.File) -> dict[str, str]:
    """Extract metadata from an MDANSE HDF5 file.

    Parameters
    ----------
    hdf5_file : h5py.File
        MDANSE output file, .mda or .mdt

    Returns
    -------
    dict[str, str]
        dictionary of saved input information used to create the file

    """
    meta_dict = {}

    def put_into_dict(name: str, obj: bytes):
        """Put an entry from an HDF5 dataset into a dictionary, as string.

        This helper function is used together with the visititems method
        of HDF5 datasets, provided by h5py. It will be called for each
        dataset in the 'metadata' group, and it will try to convert
        the contents of that dataset to string, which will then be stored
        in the meta_dict dictionary.

        Parameters
        ----------
        name : str
            name (key) of the dataset from an HDF5 group
        obj : bytes
            contents of the dataset (text stored as 'bytes')
        """
        try:
            string = obj[:][0]
        except TypeError:
            try:
                string = obj[0]
            except TypeError:
                return
        try:
            string = string.decode()
        except KeyError:
            LOG.debug(f"Decode failed for {name}: {obj}")
            meta_dict[name] = str(obj)
        else:
            try:
                meta_dict[name] = json_decoder.decode(string)
            except ValueError:
                meta_dict[name] = string

    try:
        meta = hdf5_file["metadata"]
    except KeyError:
        return
    else:
        meta.visititems(put_into_dict)

    meta_dict["<b>file header</b>"] = "\n" + hdf5_file.attrs.get("header", "no header")

    return meta_dict


def write_metadata(job: IJob, output_file: h5py.File):
    """Save parameters of IJob in the output file.

    Parameters
    ----------
    job : IJob
        IJob instance, typically Converter
    output_file : h5py.File
        an open HDF5 file, typically .mdt

    """
    string_dt = h5py.special_dtype(vlen=str)
    meta = output_file.create_group("metadata")
    meta.create_dataset("task_name", (1,), data=type(job).__name__, dtype=string_dt)
    meta.create_dataset(
        "MDANSE_version",
        (1,),
        data=str(metadata.version("MDANSE")),
        dtype=string_dt,
    )

    inputs = job.output_configuration()

    if inputs is not None:
        LOG.info(inputs)
        dgroup = meta.create_group("inputs")
        for key, value in inputs.items():
            dgroup.create_dataset(key, (1,), data=value, dtype=string_dt)


class HDFFormat(IFormat):
    """Handles the writing of output variables in HDF file format.

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
        filename: Path | str,
        data: dict[str, IOutputVariable],
        header: str = "",
        run_instance: IJob | None = None,
        extension: str | None = None,
        *,
        in_memory: bool = False,
    ) -> None | h5py.File:
        """Write a set of output variables into an HDF file.

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
        in_memory : bool
            if True, no file is created and the data structure is returned

        Returns
        -------
        None | h5py.File
            ``None`` if not ``in_memory``, otherwise the "written" datafile.
        """
        if extension is None:
            extension = cls.extensions[0]

        string_dt = h5py.special_dtype(vlen=str)

        if in_memory:
            outputFile = h5py.File.in_memory()

        else:
            filename = Path(filename).with_suffix(extension)

            # The HDF output file is opened for writing.
            PLATFORM.create_directory(filename.parent)
            outputFile = h5py.File(filename, "w")

        if header:
            # This is to avoid any segmentation fault when writing the HDF header field
            header = str(header)

            outputFile.attrs["header"] = header

        meta = outputFile.create_group("metadata")
        if run_instance is not None:
            meta.create_dataset(
                "task_name",
                (1,),
                data=type(run_instance).__name__,
                dtype=string_dt,
            )
            meta.create_dataset(
                "MDANSE_version",
                (1,),
                data=str(metadata.version("MDANSE")),
                dtype=string_dt,
            )

            if inputs := run_instance.output_configuration():
                LOG.info(inputs)
                dgroup = meta.create_group("inputs")
                for key, value in inputs.items():
                    dgroup.create_dataset(key, (1,), data=value, dtype=string_dt)

        # Loop over the OutputVariable instances to write.

        for var in data.values():
            # h5py.File.create_dataset natively supports `create_data("a/b/c", ...)` and will create parents.
            varName = str(var.varname).strip()

            dset = outputFile.create_dataset(varName, data=var, shape=var.shape)

            # All the attributes stored in the OutputVariable instance are written to the HDF file.
            for k, v in vars(var).items():
                dset.attrs[k] = v

        # The HDF file is closed.
        if in_memory:
            return outputFile
        outputFile.close()
        return None
