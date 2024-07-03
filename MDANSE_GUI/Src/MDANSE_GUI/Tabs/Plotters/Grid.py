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

from typing import TYPE_CHECKING, List
import math

from MDANSE.Framework.Units import measure
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Grid(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._backup_limits = []

    def slider_labels(self) -> List[str]:
        return ["Inactive", "Inactive"]

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "Figure" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        target = self.get_figure(figure)
        self.get_mpl_colors()
        if colours is not None:
            self._current_colours = colours
        number_of_colours = len(self._current_colours)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        self._axes = []
        self.apply_settings(plotting_context, colours)
        nplots = 0
        for databundle in plotting_context.datasets().values():
            ds, colour, style, _ = databundle
            best_unit, best_axis = ds.longest_axis()
            curves = ds.curves_vs_axis(best_unit)
            nplots += len(curves)
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for name, databundle in plotting_context.datasets().items():
            dataset, colour, style, ds_num = databundle
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
                xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
                try:
                    new_limits = self._backup_limits[ds_num]
                except IndexError:
                    while len(self._backup_limits) < (ds_num + 1):
                        self._backup_limits.append([])
                if not update_only:
                    self._backup_limits[ds_num] = [
                        xlimits[0],
                        xlimits[1],
                        ylimits[0],
                        ylimits[1],
                    ]
                else:
                    axes.set_xlim((new_limits[0], new_limits[1]))
                    axes.set_ylim((new_limits[2], new_limits[3]))
                axes.grid(True)
                axes.set_xlabel(xaxis_unit)
                axes.legend(loc=0)
                startnum += 1
        self.apply_settings(plotting_context, colours)
        target.canvas.draw()