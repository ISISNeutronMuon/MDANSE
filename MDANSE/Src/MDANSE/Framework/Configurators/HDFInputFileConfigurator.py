# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/HDFInputFileConfigurator.py
# @brief     Implements module/class/test HDFInputFileConfigurator
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
    This configurator allows to input an HDF file as input file.
    """

    _default = "INPUT_FILENAME.mda"

    def __init__(self, name, variables=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param variables: the list of HDF variables that must be present in the input HDF file or None if there is no compulsory variable.
        :type variables: list of str or None
        """

        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)

        self._variables = variables if variables is not None else []
        self._units = {}

    def configure(self, value):
        """
        Configure a HDF file.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the HDF file.
        :type value: str
        """

        InputFileConfigurator.configure(self, value)
        if not self._valid:
            return

        try:
            self["instance"] = h5py.File(self["value"], "r")

        except IOError:
            self.error_status = f"can not open {value} HDF file for reading"
            return

        for v in self._variables:
            if v in self["instance"]:
                self[v] = self["instance"][v][:]
                try:
                    self._units[v] = self["instance"][v].attrs["units"]
                except:
                    self._units[v] = "unitless"
            else:
                self.error_status = (
                    f"the variable {v} was not  found in {value} HDF file"
                )
                return
        self.error_status = "OK"

    @property
    def variables(self):
        """
        Returns the list of HDF variables that must be present in the HDF file.

        :return: the list of HDF variables that must be present in the HDF file.
        :rtype: list of str
        """

        return self._variables

    def get_information(self):
        """
        Returns some basic informations about the contents of the HDF file.

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
