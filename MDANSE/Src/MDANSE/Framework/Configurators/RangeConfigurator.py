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
from __future__ import annotations

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
)


class RangeConfigurator(IConfigurator):
    """Inputs a range of values as 3 parameters : start, stop, step.

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

        self.valueType = valueType

        self.includeLast = includeLast

        self.sort = sort

        self.toList = toList

        self.mini = mini

        self.maxi = maxi

    def configure(self, value):
        """
        Configure a range from its first, last and step values.

        :param value: the first, last and step values used to generate the range.
        :type value: 3-tuple
        """

        self._original_input = value

        first, last, step = value

        if step == 0:
            self.error_status = "Step of a range cannot be 0"
            return

        if self.includeLast:
            last += step * 0.01  # less likely to overstep the upper limit

        value = np.arange(first, last, step)
        # we add additional check if the points are all within limits
        value = value[np.where(value >= first)]
        if self.includeLast:
            value = value[np.where(value <= last)]
        else:
            value = value[np.where(value < last)]
        # end of the range check
        value = value.astype(self.valueType)

        if self.mini is not None:
            value = value[value >= self.mini]

        if self.maxi is not None:
            value = value[value < self.maxi]

        if value.size == 0:
            self.error_status = "the input range is empty."
            return

        if self.sort:
            value = np.sort(value)

        if self.toList:
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
