import abc
import collections

import numpy as np

import netCDF4

import h5py

from MDANSE.Core.Decorators import compatibleabstractproperty
from MDANSE.IO.NetCDF import find_numeric_variables as netcdf_find_numeric_variables
from MDANSE.IO.HDF5 import find_numeric_variables as hdf_find_numeric_variables


class _IPlotterData(metaclass=abc.ABCMeta):
    """
    This is the interface for plotter data.

    Plotter data are data supported by the plotter. Currently, only NetCDF is supported but HDF should be supported soon.
    """

    @abc.abstractmethod
    def __init__(self):
        self._file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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

        self._variables = netcdf_find_numeric_variables(
            collections.OrderedDict(), self._file
        )

    @property
    def variables(self):
        return self._variables


class HDFPlotterData(_IPlotterData):
    """This class implements the plotter data interface for HDF data."""

    def __init__(self, *args, **kwargs):
        """Constructor. It takes any arguments that can be passed to HDF.File to create an instance of it."""

        self._file = h5py.File(*args, **kwargs)

        self._variables = collections.OrderedDict()

        hdf_find_numeric_variables(self._variables, self._file)

    @property
    def variables(self):
        return self._variables


PLOTTER_DATA_TYPES = {
    ".nc": NetCDFPlotterData,
    ".cdf": NetCDFPlotterData,
    ".netcdf": NetCDFPlotterData,
    ".hdf": HDFPlotterData,
    ".h5": HDFPlotterData,
}
