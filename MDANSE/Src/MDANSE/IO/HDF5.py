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

import h5py
import numpy as np

from MDANSE.IO.IOUtils import _IFileVariable


class HDFFileVariable(_IFileVariable):
    """Wrapper for HDF plotter data."""

    def get_array(self):
        """Returns the actual data stored by the plotter data.

        :return: the data
        :rtype: numpy array
        """
        return self._variable[:]

    def get_attributes(self):
        """Returns the attributes stored by the plotter data.

        :return: the attributes
        :rtype: dict
        """
        return self._variable.attrs


def find_numeric_variables(var_dict, group):
    """
    Recursively retrieves all the numeric variables stored in an HDF5 file.

    :param var_dict: The dictionary into which the variables are saved.
    :type var_dict: dict

    :param group: The file whose variables are to be retrieved.
    :type group: h5py.File or h5py.Group
    """

    for var_key, var in list(group.items()):
        if isinstance(var, h5py.Group):
            find_numeric_variables(var_dict, var)
        else:
            if var.parent.name == "/":
                path = "/{}".format(var_key)
            else:
                path = "{}/{}".format(var.parent.name, var_key)

            # Non-numeric variables are not supported by the plotter
            if not np.issubdtype(var.dtype, np.number):
                continue

            # Variables with dimension higher than 3 are not supported by the plotter
            if var.ndim > 3:
                continue

            comp = 1
            while var_key in var_dict:
                var_key = "{:s}_{:d}".format(var_key, comp)
                comp += 1

            var_dict[var_key] = (path, HDFFileVariable(var))
