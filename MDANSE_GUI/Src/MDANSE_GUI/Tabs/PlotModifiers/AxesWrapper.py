#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.axis import Axis


class AxesWrapper:
    def __init__(self, *args, **kwargs):
        self._axes = kwargs.pop("axes", None)
        self._plot_elements = []

    @property
    def axes(self):
        return self._axes

    def clear(self):
        self._plot_elements = []
        self._axes.clear()

    def plot(self, *args, **kwargs):
        curve = self._axes.plot(*args, **kwargs)
        self._plot_elements.append(curve)
        return curve
