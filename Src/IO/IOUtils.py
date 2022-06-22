# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/IInputData.py
# @brief     Implements module/class/test IInputData
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
from collections import OrderedDict

import numpy


class _IFileVariable:
    """This is the abstract base class for file variable.

    Basically, this class allows to have a common interface for the data formats supported by MDANSE.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, variable):
        self._variable = variable

    def __getattr__(self, name):
        return getattr(self._variable, name)

    def __hasattr__(self, name):
        return hasattr(self._variable, name)

    @property
    def variable(self):
        return self._variable

    @abc.abstractmethod
    def get_array(self):
        """Returns the actual data stored by the plotter data.

        :return: the data
        :rtype: numpy array
        """
        pass

    @abc.abstractmethod
    def get_attributes(self):
        """Returns the attributes stored by the plotter data.

        :return: the attributes
        :rtype: dict
        """
        pass


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


def netcdf_find_numeric_variables(var_dict, group):
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
        var_dict.update(netcdf_find_numeric_variables(var_dict, sub_group))

    return var_dict


def load_variables(dictionary):
    """
    Processes the provided variables into a form usable by MDANSE. This is done by moving the various attributes and
    properties of each variable into a dictionary.

    :param dictionary: The variables to be processed.
    :type dictionary: dict[str, (str, _IFileVariable)]

    :return: The processed variables.
    :rtype: collections.OrderedDict[str, dict]
    """
    data = OrderedDict()
    for vname, vinfo in dictionary.items():
        vpath, variable = vinfo
        arr = variable.get_array()
        attributes = variable.get_attributes()

        data[vname] = {}
        if 'axis' in attributes:
            axis = attributes['axis']
            if axis:
                data[vname]['axis'] = axis.split('|')
            else:
                data[vname]['axis'] = []
        else:
            data[vname]['axis'] = []
        data[vname]['path'] = vpath
        data[vname]['data'] = arr
        data[vname]['units'] = attributes.get('units', 'au')

    return data
