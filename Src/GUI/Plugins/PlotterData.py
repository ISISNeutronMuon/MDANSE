import abc
import collections

import numpy

import netCDF4

from MDANSE.Core.Decorators import compatibleabstractproperty

class _IPlotterVariable:

    __metaclass__ = abc.ABCMeta

    def __init__(self, variable):

        self._variable = variable

    def __getattr__(self,name):
        return getattr(self._variable,name)

    def __hasattr__(self,name):

        return hasattr(self._variable,name)

    @abc.abstractmethod
    def get_array(self):
        pass

class NetCDFPlotterVariable(_IPlotterVariable):

    def get_array(self):
        return self._variable[:]

class _IPlotterData:

    __metaclass__ = abc.ABCMeta

    @compatibleabstractproperty
    def variables(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    def __del__(self):        
        self.close()

class NetCDFPlotterData(_IPlotterData):

    def __init__(self, *args, **kwargs):

        self._netcdf = netCDF4.Dataset(*args, **kwargs)

        self._variables = collections.OrderedDict()
        NetCDFPlotterData.find_numeric_variables(self._variables,self._netcdf)

    def close(self):
        self._netcdf.close()

    @property
    def variables(self):
        return self._variables

    @staticmethod
    def find_numeric_variables(var_dict, group):
        for var_key, var in group.variables.items():
            var_name = '{}{}'.format(group.path,var_key)
            if not numpy.issubdtype(var.dtype,numpy.number):
                continue
            if var.ndim > 3:
                continue
            var_dict[var_name] = NetCDFPlotterVariable(var)

        for _, sub_group in group.groups.items():
            NetCDFPlotterData.find_numeric_variables(var_dict, sub_group)

PLOTTER_DATA_TYPES = {NetCDFPlotterData:('.nc','.cdf','.netcdf')}
