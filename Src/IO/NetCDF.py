# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/IInputData.py
# @brief     Implements module/class/test IInputData
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy

from MDANSE.IO.IOUtils import _IFileVariable


class NetCDFFileVariable(_IFileVariable):
    """Wrapper for NetCDF plotter data."""

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
        return self._variable.__dict__


def find_numeric_variables(var_dict, group):
    """
    This function recursively retrieves all the numeric variables stored in a NetCDF file.

    :param var_dict: The dictionary into which the variables are saved.
    :type var_dict: dict

    :param group: The file whose variables are to be retrieved.
    :type group: netCDF4.Dataset or netCDF4.Group

    :return: All the variable objects in the provided file.
    :rtype: collections.OrderedDict[str, (str, NetCDFFileVariable)]
    """

    for var_key, var in group.variables.items():
        if group.path == '/':
            path = '/{}'.format(var_key)
        else:
            path = '{}/{}'.format(group.path, var_key)

        # Non-numeric variables are not supported
        if not numpy.issubdtype(var.dtype, numpy.number):
            continue
        # Variables with dimension higher than 3 are not supported
        if var.ndim > 3:
            continue

        comp = 1
        while var_key in var_dict:
            var_key = '{:s}_{:d}'.format(var_key, comp)
            comp += 1

        var_dict[var_key] = (path, NetCDFFileVariable(var))

    for _, sub_group in group.groups.items():
        var_dict.update(find_numeric_variables(var_dict, sub_group))

    return var_dict
