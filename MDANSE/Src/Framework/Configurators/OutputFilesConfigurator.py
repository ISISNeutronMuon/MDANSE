# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/OutputFilesConfigurator.py
# @brief     Implements module/class/test OutputFilesConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import tempfile

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class OutputFilesConfigurator(IConfigurator):
    """
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from an analysis.

    Once configured, this configurator will provide a list of files built by joining the given output directory, the
    basename and the extensions corresponding to the input file formats.

    For analysis, MDANSE currently supports only the HDF, NetCDF, SVG and ASCII formats. To define a new output file format
    for an analysis, you must inherit from MDANSE.Framework.Formats.IFormat.IFormat interface.
    """

    _default = (os.path.join(tempfile.gettempdir(), "output"), ["hdf"])

    def __init__(self, name, formats=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param formats: the list of output file formats supported.
        :type formats: list of str
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._formats = (
            formats if formats is not None else OutputFilesConfigurator._default[-1]
        )

    def configure(self, value):
        """
        Configure a set of output files for an analysis.

        :param value: the output files specifications. Must be a 3-tuple whose 1st element \
        is the output directory, 2nd element the basename and 3rd element a list of file formats.
        :type value: 3-tuple
        """

        root, formats = value

        if not root:
            raise ConfiguratorError("empty root name for the output file.", self)

        dirname = os.path.dirname(root)

        try:
            PLATFORM.create_directory(dirname)
        except:
            raise ConfiguratorError("the directory %r is not writable" % dirname)

        if not formats:
            raise ConfiguratorError("no output formats specified", self)

        for fmt in formats:
            if not fmt in self._formats:
                raise ConfiguratorError(
                    "the output file format %r is not a valid output format" % fmt, self
                )

            if fmt not in REGISTRY["format"]:
                raise ConfiguratorError(
                    "the output file format %r is not registered as a valid file format."
                    % fmt,
                    self,
                )

        self["root"] = root
        self["formats"] = formats
        self["files"] = [
            "%s%s" % (root, REGISTRY["format"][f].extension) for f in formats
        ]

        self["value"] = self["files"]

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

        info = ["Input files:\n"]
        for f in self["files"]:
            info.append(f)
            info.append("\n")

        return "".join(info)


REGISTRY["output_files"] = OutputFilesConfigurator
