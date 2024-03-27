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
# Copyright (C)  Institut Laue Langevin 2023-now
# Authors:    Eric Pellegrini

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class PreviewWidget(FigureCanvasQTAgg):
    def __init__(self, *args, **kwargs):
        """Constructor."""
        fig = Figure(figsize=(2, 2))
        self._axes = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        super(PreviewWidget, self).__init__(fig, *args, **kwargs)

    def update_plot(self, data_info):
        """Update the previes plot.

        Args:
            data_info (dict): the information about the data to preview
        """
        self._axes.clear()

        if not data_info["plottable"]:
            self._axes.text(0.2, 0.5, "Data not plottable")
        else:
            ndim = data_info["dimension"]
            if ndim == 1:
                self._axes.plot(data_info["data"])
                self._axes.legend([data_info["variable"]])

            elif ndim == 2:
                self._axes.imshow(
                    data_info["data"], interpolation="nearest", origin="lower"
                )

            else:
                self._axes.text(0.2, 0.5, "No preview available")

        self._axes.set_aspect("auto")
        self.draw()
