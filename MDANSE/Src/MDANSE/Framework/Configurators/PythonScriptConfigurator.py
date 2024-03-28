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


from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator


class PythonScriptConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a Python script.
    """

    _default = ""

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

    def configure(self, value):
        """
        Configure a python script.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the python script.
        :type value: str
        """

        InputFileConfigurator.configure(self, value)

        namespace = {}

        exec(compile(open(value, "rb").read(), value, "exec"), self.__dict__, namespace)

        for v in self._variables:
            if v not in namespace:
                self.error_status = (
                    f"The variable {v} is not defined in the {value} python script file"
                )
                return

        self.update(namespace)
        self.error_status = "OK"

    @property
    def variables(self):
        """
        Returns the list of HDF variables that must be present in the HDF file.

        :return: the list of HDF variables that must be present in the HDF file.
        :rtype: list of str
        """

        return self._variables
