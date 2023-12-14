# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/NetCDFInputFileConfigurator.py
# @brief     Implements module/class/test NetCDFInputFileConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import h5py


from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.IO.HDF import find_numeric_variables


class HDFInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a HDF file as input file.
    """

    _default = ""

    def __init__(self, name, variables=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param variables: the list of NetCDF variables that must be present in the input NetCDF file or None if there is no compulsory variable.
        :type variables: list of str or None
        """

        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)

        self._variables = variables if variables is not None else []

    def configure(self, value):
        """
        Configure a NetCDF file.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the NetCDF file.
        :type value: str
        """

        InputFileConfigurator.configure(self, value)

        try:
            self["instance"] = h5py.File(self["value"], "r")

        except IOError:
            raise ConfiguratorError(
                "can not open %r NetCDF file for reading" % self["value"]
            )

        for v in self._variables:
            if v in self["instance"]:
                self[v] = self["instance"][v][:]
            else:
                raise ConfiguratorError(
                    "the variable %r was not  found in %r NetCDF file"
                    % (v, self["value"])
                )

    @property
    def variables(self):
        """
        Returns the list of NetCDF variables that must be present in the NetCDF file.

        :return: the list of NetCDF variables that must be present in the NetCDF file.
        :rtype: list of str
        """

        return self._variables

    def get_information(self):
        """
        Returns some basic informations about the contents of theHDF file.

        :return: the informations about the contents of the HDF file.
        :rtype: str
        """

        info = ["HDF input file: %r" % self["value"]]

        if "instance" in self:
            info.append("Contains the following variables:")
            variables = []
            find_numeric_variables(variables, self["instance"])

            for v in variables:
                info.append("\t-{}".format(v))

        return "\n".join(info)
