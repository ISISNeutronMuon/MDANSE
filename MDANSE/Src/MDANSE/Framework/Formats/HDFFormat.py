# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE/Framework/Formats/HDFFormat.py
# @brief     Implements module/class/test HDFFormat
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
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
    def write(cls, filename: str, data: dict[str, IOutputVariable],
              header: str = "",
              extension: str = extensions[0]) -> None:
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
