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

import h5py
import numpy

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

    for var_key, var in group.items():

        if isinstance(var, h5py.Group):
            find_numeric_variables(var_dict, var)
        else:

            if var.parent.name == '/':
                path = '/{}'.format(var_key)
            else:
                path = '{}/{}'.format(var.parent.name, var_key)

            # Non-numeric variables are not supported by the plotter
            if not numpy.issubdtype(var.dtype, numpy.number):
                continue

            # Variables with dimension higher than 3 are not supported by the plotter
            if var.ndim > 3:
                continue

            comp = 1
            while var_key in var_dict:
                var_key = '{:s}_{:d}'.format(var_key, comp)
                comp += 1

            var_dict[var_key] = (path, HDFFileVariable(var))
