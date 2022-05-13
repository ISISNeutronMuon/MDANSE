import abc
import collections

import numpy

import netCDF4

from MDANSE.Core.Decorators import compatibleabstractproperty

class _IPlotterVariable:
    """This is the base abstract class for plotter variable.

    Basically, this class allows to have a common interface for the data supported by the plotter (netcdf currently, hdf in the future, ...)
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, variable):

        self._variable = variable

    def __getattr__(self,name):
        return getattr(self._variable,name)

    def __hasattr__(self,name):

        return hasattr(self._variable,name)

    @abc.abstractmethod
    def get_array(self):
        """Returns the actual data stored by the plotter data.

        :return: the data
        :rtype: numpy array
        """
        pass

class NetCDFPlotterVariable(_IPlotterVariable):
    """Wrapper for NetCDF plotter data.
    """

    def get_array(self):
        """Returns the actual data stored by the plotter data.

        :return: the data
        :rtype: numpy array
        """
        return self._variable[:]

class _IPlotterData:
    """This is the interface for plotter data.

    Plotter data are data supported by the plotter. Currently, only NetCDF is supported but HDF should be supported soon.
    """

    __metaclass__ = abc.ABCMeta

    @compatibleabstractproperty
    def variables(self):
        pass

    def close(self):
        """Close the data.
        """
        
        self._file.close()

    def __del__(self):        
        self.close()

class NetCDFPlotterData(_IPlotterData):
    """This class implements the plotter data interface for NetCDF data.
    """

    def __init__(self, *args, **kwargs):
        """Constructor.
        """

        self._file = netCDF4.Dataset(*args, **kwargs)

        self._variables = collections.OrderedDict()

        NetCDFPlotterData.find_numeric_variables(self._variables,self._file)

    @property
    def variables(self):
        return self._variables

    @staticmethod
    def find_numeric_variables(var_dict, group):
        """This method retrieves all the variable stored in the NetCDF file.

        This is a recursive method.
        """

        for var_key, var in group.variables.items():
            var_name = '{}{}'.format(group.path,var_key)
            # Non numeric variables are not supported by the plotter
            if not numpy.issubdtype(var.dtype,numpy.number):
                continue
            # Variables with dimension higher than 3 are not supported by the plotter
            if var.ndim > 3:
                continue
            var_dict[var_name] = NetCDFPlotterVariable(var)

        for _, sub_group in group.groups.items():
            NetCDFPlotterData.find_numeric_variables(var_dict, sub_group)

PLOTTER_DATA_TYPES = {NetCDFPlotterData:('.nc','.cdf','.netcdf')}
