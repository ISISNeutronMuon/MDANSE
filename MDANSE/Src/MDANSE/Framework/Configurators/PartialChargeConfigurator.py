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
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import os


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Framework.UserDefinitionStore import UD_STORE


class PartialChargeConfigurator(IConfigurator):
    """
    This configurator allows to input partial charges.
    """

    _default = ""

    def configure(self, value):
        """
        Configure a python script.

        :param value: the path for the python script.
        :type value: str
        """

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        if UD_STORE.has_definition(trajConfig["basename"], "partial_charges", value):
            self.update(
                UD_STORE.get_definition(
                    trajConfig["basename"], "partial_charges", value
                )
            )
        else:
            if isinstance(value, str):
                # Case of a python script
                if os.path.exists(value):
                    namespace = {}

                    exec(
                        compile(open(value, "rb").read(), value, "exec"),
                        self.__dict__,
                        namespace,
                    )

                    if "charges" not in namespace:
                        self.error_status = (
                            f"The variable 'charges' is not defined in"
                            f"the {value} python script file"
                        )
                        return

                    self.update(namespace)
                else:
                    self.error_status = f"The python script defining partial charges {value} could not be found."
                    return

            elif isinstance(value, dict):
                self["charges"] = value
            else:
                self.error_status = f"Invalid type for partial charges."
                return
        self.error_status = "OK"

    def get_information(self):
        """
        Returns some basic informations about the partial charges.

        :return: the informations about the partial charges.
        :rtype: str
        """

        info = "Sum of partial charges = %8.3f\n" % sum(self["charges"].values())

        return info
