import abc
import collections

import numpy

import netCDF4

from MDANSE.Core.Decorators import compatibleabstractproperty

class IPlotterData:

    __metaclass__ = abc.ABCMeta

    @compatibleabstractproperty
    def variables(self):
        pass

class NetCDFPlotterData(IPlotterData):

    def __init__(self, *args, **kwargs):

        self._netcdf = netCDF4.Dataset(*args, **kwargs)

        self._variables = collections.OrderedDict()
        NetCDFPlotterData.find_numeric_variables(self._variables,self._netcdf)

    @property
    def variables(self):
        return self._variables

    @staticmethod
    def find_numeric_variables(var_dict, group):
        for var_key, var in group.variables.items():
            var_name = '{}/{}'.format(group.path,var_key)
            if not numpy.issubdtype(var.dtype,numpy.number):
                continue
            var_dict[var_name] = var

        for _, sub_group in group.groups.items():
            NetCDFPlotterData.find_numeric_variables(var_dict, sub_group)

PLOTTER_DATA_TYPES = {NetCDFPlotterData:('.nc','.cdf')}
