import abc
import collections

import numpy

import netCDF4

import h5py

from MDANSE.Core.Decorators import compatibleabstractproperty


class _IPlotterVariable:
    """This is the base abstract class for plotter variable.

    Basically, this class allows to have a common interface for the data supported by the plotter (netcdf currently,
    hdf in the future, ...)
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


class NetCDFPlotterVariable(_IPlotterVariable):
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


class HDFPlotterVariable(_IPlotterVariable):
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


class _IPlotterData:
    """
    This is the interface for plotter data.

    Plotter data are data supported by the plotter. Currently, only NetCDF is supported but HDF should be supported soon.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        self._file = None

    def __enter__(self):
        return self

    def  __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @compatibleabstractproperty
    def variables(self):
        pass

    def close(self):
        """Close the data."""
        self._file.close()
        

class NetCDFPlotterData(_IPlotterData):
    """This class implements the plotter data interface for NetCDF data."""

    def __init__(self, *args, **kwargs):
        """Constructor. It takes any arguments that can be passed to netCDF4.Dataset to create an instance of it."""

        self._file = netCDF4.Dataset(*args, **kwargs)

        self._variables = collections.OrderedDict()

        NetCDFPlotterData.find_numeric_variables(self._variables, self._file)

    @property
    def variables(self):
        return self._variables

    @staticmethod
    def find_numeric_variables(var_dict, group):
        """This method retrieves all the numeric variables stored in the NetCDF file.

        This is a recursive method.
        """

        for var_key, var in group.variables.items():
            if group.path == '/':
                path = '/{}'.format(var_key)
            else:
                path = '{}/{}'.format(group.path, var_key)

            # Non numeric variables are not supported by the plotter
            if not numpy.issubdtype(var.dtype, numpy.number):
                continue
            # Variables with dimension higher than 3 are not supported by the plotter
            if var.ndim > 3:
                continue

            comp = 1
            while var_key in var_dict:
                var_key = '{:s}_{:d}'.format(var_key, comp)
                comp += 1

            var_dict[var_key] = (path, NetCDFPlotterVariable(var))

        for _, sub_group in group.groups.items():
            NetCDFPlotterData.find_numeric_variables(var_dict, sub_group)


class HDFPlotterData(_IPlotterData):
    """This class implements the plotter data interface for HDF data."""

    def __init__(self, *args, **kwargs):
        """Constructor. It takes any arguments that can be passed to HDF.File to create an instance of it."""

        self._file = h5py.File(*args, **kwargs)

        self._variables = collections.OrderedDict()

        HDFPlotterData.find_numeric_variables(self._variables, self._file)

    @property
    def variables(self):
        return self._variables

    @staticmethod
    def find_numeric_variables(var_dict, group):
        """This method retrieves all the numeric variables stored in the NetCDF file.

        This is a recursive method.
        """

        for var_key, var in group.items():

            if isinstance(var,h5py.Group):
                HDFPlotterData.find_numeric_variables(var_dict,var)
            else:

                if var.parent.name == '/':
                    path = '/{}'.format(var_key)
                else:
                    path = '{}/{}'.format(var.parent.name, var_key)

                # Non numeric variables are not supported by the plotter
                if not numpy.issubdtype(var.dtype, numpy.number):
                    continue

                # Variables with dimension higher than 3 are not supported by the plotter
                if var.ndim > 3:
                    continue

                comp = 1
                while var_key in var_dict:
                    var_key = '{:s}_{:d}'.format(var_key, comp)
                    comp += 1

                var_dict[var_key] = (path,HDFPlotterVariable(var))

PLOTTER_DATA_TYPES = {
    '.nc': NetCDFPlotterData,
    '.cdf': NetCDFPlotterData,
    '.netcdf': NetCDFPlotterData,
    '.hdf': HDFPlotterData,
    '.h5': HDFPlotterData}
