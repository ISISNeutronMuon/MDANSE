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


@IConfigurator.register("RangeConfigurator")
class RangeConfigurator(IConfigurator):
    """Inputs a range of values as 3 parameters : start, stop, step.

    By default the values are generated as a NumPy array.
    """

    _default = (0, 10, 1)

    def __init__(
        self,
        name: str,
        valueType: type = int,
        includeLast: bool = False,
        sort: bool = False,
        toList: bool = False,
        mini: int | float | None = None,
        maxi: int | float | None = None,
        **kwargs,
    ):
        """
        Initializes the configurator.

        Parameters
        ----------
        name : str
            The name of the configurator as it will appear in the configuration.
        valueType : type
            The numeric type for the range, `int` or `float`.
        includeLast : bool
            If True the last value of the interval will be included (closed interval) otherwise excluded (opened interval).
        sort : bool
            If True, the values generated will be sorted in increasing order.
        toList : bool
            If True, the values generated will be converted from a NumPy array to a python list.
        mini : int or float or None
            If not None, all values generated below mini will be discarded.
        maxi : int or float or None
            If not None, all values generated over maxi will be discarded.
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

        if not isinstance(value, list | tuple):
            self.error_status = "Invalid input type."
            return

        if len(value) != 3:
            self.error_status = "The range configurator input should have three values."
            return

        first, last, step = value

        if step == 0:
            self.error_status = "Step of a range cannot be 0."
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
