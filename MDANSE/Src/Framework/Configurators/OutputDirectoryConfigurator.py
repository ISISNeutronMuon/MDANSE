# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/OutputDirectoryConfigurator.py
# @brief     Implements module/class/test OutputDirectoryConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class OutputDirectoryConfigurator(IConfigurator):
    """
    This Configurator allows to set an output directory.
    """

    _default = os.getcwd()

    def __init__(self, name, new=False, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param new: if True the output directory path will be checked for being new.
        :type new: bool
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._new = new

    def configure(self, value):
        """
        Configure an output directory.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the output directory.
        :type value: str
        """

        value = PLATFORM.get_path(value)

        if self._new:
            if os.path.exists(value):
                raise ConfiguratorError("the output directory must not exist", self)

        self["value"] = value

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Output directory: %r" % self["value"]


REGISTRY["output_directory"] = OutputDirectoryConfigurator
