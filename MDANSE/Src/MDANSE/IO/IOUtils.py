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

import abc
from collections import OrderedDict


class _IFileVariable(metaclass=abc.ABCMeta):
    """This is the abstract base class for file variable.

    Basically, this class allows to have a common interface for the data formats supported by MDANSE.
    """

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
    for vname, vinfo in list(dictionary.items()):
        vpath, variable = vinfo
        arr = variable.get_array()
        attributes = variable.get_attributes()

        data[vname] = {}
        if "axis" in attributes:
            axis = attributes["axis"]
            if axis:
                data[vname]["axis"] = axis.split("|")
            else:
                data[vname]["axis"] = []
        else:
            data[vname]["axis"] = []
        data[vname]["path"] = vpath
        data[vname]["data"] = arr
        data[vname]["units"] = attributes.get("units", "au")

    return data
