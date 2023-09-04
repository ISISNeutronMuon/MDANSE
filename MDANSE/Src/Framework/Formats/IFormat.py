# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Formats/IFormat.py
# @brief     Implements module/class/test IFormat
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


class IFormat(object):
    """
    This is the base class for writing MDANSE output data. In MDANSE, the output of an analysis can be written in different file format.

    Currently, MDANSE supports NetCDF, SVG and ASCII output file formats. To introduce a new file output file format, just create a new concrete
    subclass of IFormat and overload the "write" class method as defined in IFormat base class which will actually write the output variables,
    and redefine the "type", "extension" and "extensions" class attributes.
    """

    _registry = "format"

    @classmethod
    def write(cls, filename, data, header=""):
        """
        Write a set of output variables into filename using a given file format.

        :param filename: the path to the output file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        """

        pass
