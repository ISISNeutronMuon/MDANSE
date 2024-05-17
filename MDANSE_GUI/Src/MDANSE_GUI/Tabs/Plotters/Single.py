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


class Single(Plotter):

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
        self.get_mpl_colors()
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context, colours)
        xaxis_unit = plotting_context._current_axis[0]
        for name, dataset in plotting_context.datasets().items():
            xtags = list(dataset._axes.keys())
            plotlabel = dataset._labels["medium"]
            try:
                conversion_factor = measure(
                    1.0, dataset._axes_units[xtags[0]], equivalent=True
                ).toval(xaxis_unit)
            except:
                continue
            else:
                axes.plot(
                    dataset._axes[xtags[0]] * conversion_factor,
                    dataset._data,
                    label=plotlabel,
                )
        axes.set_xlabel(xaxis_unit)
        axes.grid(True)
        axes.legend(loc=0)
        target.canvas.draw()
