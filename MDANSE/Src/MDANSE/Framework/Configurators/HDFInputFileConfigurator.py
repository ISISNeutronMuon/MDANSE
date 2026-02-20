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

import traceback

import h5py

from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator


class HDFInputFileConfigurator(InputFileConfigurator):
    """Uses an .mda file from another analysis as input."""

    _default = ""

    def __init__(
        self,
        name,
        variables=None,
        wildcard="MDA analysis results (*.mda);;HDF5 files (*.h5);;All files (*)",
        **kwargs,
    ):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param variables: the list of HDF variables that must be present in the input HDF file or None if there is no compulsory variable.
        :type variables: list of str or None
        """

        # The base class constructor.
        super().__init__(name, **kwargs)

        self.variables = variables if variables is not None else []
        self._units = {}
        self.wildcard = wildcard

    def configure(self, value):
        """
        Configure a HDF file.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the HDF file.
        :type value: str
        """

        super().configure(value)

        if not value and self.optional:
            self.error_status = "OK"
            return

        try:
            self["instance"] = h5py.File(self["value"], "r")
        except OSError:
            self.error_status = (
                f"Cannot open {value} HDF file for reading: {traceback.format_exc()}"
            )
            return

        for v in self.variables:
            if v in self["instance"]:
                self[v] = self["instance"][v][:]
                try:
                    self._units[v] = self["instance"][v].attrs["units"]
                except Exception:
                    self._units[v] = "unitless"
            else:
                self.error_status = (
                    f"The variable {v} was not found in HDF file {value}."
                )
                return
        self.error_status = "OK"
