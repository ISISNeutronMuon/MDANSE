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

import abc
from collections import OrderedDict


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

def find_numeric_variables(var_dict, group):
    """
    Retrieves the numeric variables stored in an HDF5 file.

    :param var_dict: dict into which the variables are saved.
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

            if 'trajectory' in group.filename:
                file_path = os.path.join(TRAJECTORY_DIR, var_key + '.hdf5')
            elif 'analysis' in group.filename:
                file_path = os.path.join(ANALYSIS_DIR, var_key + '.h5')

            var_dict[var_key] = (file_path, HDFFileVariable(var))