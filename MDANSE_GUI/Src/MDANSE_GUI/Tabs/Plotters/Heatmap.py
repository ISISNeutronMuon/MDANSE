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


class Heatmap(Plotter):

    def __init__(self) -> None:
        self._figure = None
        self._current_colours = []

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def get_figure(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            print(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def plot(
        self, plotting_context: "PlottingContext", figure: "Figure" = None, colours=None
    ):
        target = self.get_figure(figure)
        if target is None:
            return
        xaxis_unit = None
        yaxis_unit = None
        self.get_mpl_colors()
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context, colours)
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        for name, databundle in plotting_context.datasets().items():
            dataset, _, _ = databundle
            if dataset._n_dim == 1:
                continue
            limits = []
            for key, value in dataset._axes_units.items():
                target_unit = plotting_context.get_conversion_factor(value)
                axis_array = dataset._axes[key]
                try:
                    conversion_factor = measure(1.0, value, equivalent=True).toval(
                        target_unit
                    )
                except:
                    limits += [axis_array[0], axis_array[-1]]
                else:
                    limits += [
                        axis_array[0] * conversion_factor,
                        axis_array[-1] * conversion_factor,
                    ]
            axes.imshow(
                dataset._data.T,
                extent=limits,
                aspect="auto",
                interpolation=None,
                cmap=plotting_context._colour_map,
            )
        axes.grid(True)
        target.canvas.draw()
