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

from typing import TYPE_CHECKING
import math

from MDANSE.Framework.Units import measure
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Grid(Plotter):

    def __init__(self) -> None:
        self._figure = None

    def plot(
        self, plotting_context: "PlottingContext", figure: "Figure" = None, colours=None
    ):
        target = self.get_figure(figure)
        self.get_mpl_colors()
        if colours is not None:
            self._current_colours = colours
        number_of_colours = len(self._current_colours)
        if target is None:
            return
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        self._axes = []
        self.apply_settings(plotting_context, colours)
        nplots = 0
        for databundle in plotting_context.datasets().values():
            ds, colour, style = databundle
            best_unit, best_axis = ds.longest_axis()
            curves = ds.curves_vs_axis(best_unit)
            nplots += len(curves)
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for name, databundle in plotting_context.datasets().items():
            dataset, colour, style = databundle
            best_unit, best_axis = dataset.longest_axis()
            xaxis_unit = plotting_context.get_conversion_factor(best_unit)
            for key, curve in dataset._curves.items():
                axes = target.add_subplot(gridsize, gridsize, startnum)
                self._axes.append(axes)
                plotlabel = dataset._labels["medium"]
                conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                    xaxis_unit
                )
                axes.plot(
                    dataset._axes[best_axis] * conversion_factor,
                    curve,
                    style,
                    color=colour,
                    label=plotlabel + ":" + dataset._curve_labels[key],
                )
                axes.grid(True)
                axes.set_xlabel(xaxis_unit)
                axes.legend(loc=0)
                startnum += 1
        self.apply_settings(plotting_context, colours)
        target.canvas.draw()
