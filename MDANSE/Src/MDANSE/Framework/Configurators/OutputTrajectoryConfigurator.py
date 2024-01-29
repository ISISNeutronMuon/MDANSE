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

import numpy as np

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class OutputTrajectoryConfigurator(IConfigurator):
    """
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s)
    resulting from a trajectory conversion.

    Once configured, this configurator will provide a list of files built by joining the given output directory,
    the basename and the  extensions corresponding to the input file formats.

    For trajectories, MDANSE supports only the HDF format. To define a new output file format for a trajectory
    conversion, you must inherit from the MDANSE.Framework.Formats.IFormat.IFormat interface.
    """

    _default = ("OUTPUT_TRAJECTORY", 64, "none")

    def __init__(self, name, format=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param formats: the list of output file formats supported.
        :type formats: list of str
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._format = "MDTFormat"
        self._dtype = np.float64
        self._compression = "none"

    def configure(self, value: tuple):

        root, dtype, compression = value

        if not root:
            raise ConfiguratorError("empty root name for the output file.", self)

        dirname = os.path.dirname(root)

        try:
            PLATFORM.create_directory(dirname)
        except:
            raise ConfiguratorError("the directory %r is not writable" % dirname)

        if dtype < 17:
            self._dtype = np.float16
        elif dtype < 33:
            self._dtype = np.float32
        elif dtype < 65:
            self._dtype = np.float64
        elif dtype < 129:
            self._dtype = np.float128
        else:
            self._dtype = np.float64

        if compression in TrajectoryWriter.allowed_compression:
            self._compression = compression
        else:
            self._compression = None

        self["root"] = root
        self["format"] = self._format
        self["extension"] = IFormat.create(self._format).extension
        temp_name = root
        if not self["extension"] in temp_name[-5:]:  # capture most extension lengths
            temp_name += self["extension"]
        self["file"] = temp_name
        self["dtype"] = self._dtype
        self["compression"] = self._compression

    @property
    def format(self):
        """
        Returns the output file format supported.

        :return: the file format supported.
        :rtype: str
        """
        return self._format

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        info = "Output file: %s" % self["file"]

        return info

    @property
    def default(self) -> tuple[str, type, str]:
        """Default output parameters for a trajectory:
        uncompressed trajectory of 64-bit floating point
        numbers.

        Returns
        -------
        tuple[str, type, str]
            filename, float format, compression (string)
        """
        return self._default[0], np.float64, "none"
