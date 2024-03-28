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

import numpy as np


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class RangeConfigurator(IConfigurator):
    """
    This configurator allow to input a range of values given 3 parameters : start, stop, step.

    By default the values are generated as a NumPy array.
    """

    _default = (0, 10, 1)

    def __init__(
        self,
        name,
        valueType=int,
        includeLast=False,
        sort=False,
        toList=False,
        mini=None,
        maxi=None,
        **kwargs,
    ):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param valueType: the numeric type for the range.
        :type valueType: int or float
        :param includeLast: if True the last value of the interval will be included (closed interval) otherwise excluded (opened interval).
        :type includeLast: bool
        :param sort: if True, the values generated will be sorted in increasing order.
        :type bool: if True, the values generated will be converted from a NumPy array to a python list.
        :param toList:
        :type toList: bool
        :param mini: if not None, all values generated below mini will be discarded.
        :type mini: int, float or None
        :param maxi: if not None, all values generated over maxi will be discarded.
        :type maxi: int, float or None
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._valueType = valueType

        self._includeLast = includeLast

        self._sort = sort

        self._toList = toList

        self._mini = mini

        self._maxi = maxi

    def configure(self, value):
        """
        Configure a range from its first, last and step values.

        :param value: the first, last and step values used to generate the range.
        :type value: 3-tuple
        """

        first, last, step = value

        if step == 0:
            self.error_status = "Step of a range cannot be 0"
            return

        if self._includeLast:
            last += step * 0.01  # less likely to overstep the upper limit

        value = np.arange(first, last, step)
        # we add additional check if the points are all within limits
        value = value[np.where(value >= first)]
        if self._includeLast:
            value = value[np.where(value <= last)]
        else:
            value = value[np.where(value < last)]
        # end of the range check
        value = value.astype(self._valueType)

        if self._mini is not None:
            value = value[value >= self._mini]

        if self._maxi is not None:
            value = value[value < self._maxi]

        if value.size == 0:
            self.error_status = "the input range is empty."
            return

        if self._sort:
            value = np.sort(value)

        if self._toList:
            value = value.tolist()

        self["value"] = value

        self["first"] = self["value"][0]

        self["last"] = self["value"][-1]

        self["number"] = len(self["value"])

        self["mid_points"] = (value[1:] + value[0:-1]) / 2.0

        try:
            self["step"] = self["value"][1] - self["value"][0]
        except IndexError:
            self["step"] = 1
        self.error_status = "OK"

    @property
    def valueType(self):
        """
        Returns the values type of the range.

        :return: the values type of the range.
        :rtype: one of int or float
        """

        return self._valueType

    @property
    def includeLast(self):
        """
        Returns whether or not the range will be closed (True) or opened (False).

        :return: True if the generated range is closed, otherwise False.
        :rtype: bool
        """

        return self._includeLast

    @property
    def toList(self):
        """
        Returns whether or not the range will be generated a Numpy array (True) or python list (False).

        :return: True if the generated range is a python list, otherwise it is a Numpy array.
        :rtype: bool
        """

        return self._toList

    @property
    def sort(self):
        """
        Returns whether or not the generated values will be sorted in increasing order.

        :return: True if the generated values are sorted in in creasing order, False otherwise.
        :rtype: bool
        """

        return self._sort

    @property
    def mini(self):
        """
        Returns the minimum value for the range, None if no limit.

        :return: the minimum value for the range, None if no limit.
        :rtype: int or float
        """

        return self._mini

    @property
    def maxi(self):
        """
        Returns the maximum value for the range, None if no limit.

        :return: the maximum value for the range, None if no limit.
        :rtype: int or float
        """

        return self._maxi

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        info = "%d values from %s to %s" % (self["number"], self["first"], self["last"])

        if self._includeLast:
            info += " last value included"
        else:
            info += " last value excluded"

        return info + "\n"
