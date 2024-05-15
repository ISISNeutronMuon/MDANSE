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

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Grid(Plotter):

    def __init__(self) -> None:
        self._figure = None

    def plot(self, plotting_context: "PlottingContext", figure: "Figure" = None):
        target = self.get_figure(figure)
        if target is None:
            return
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        nplots = len(plotting_context._datasets)
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for name, dataset in plotting_context._datasets.items():
            axes = target.add_subplot(gridsize, gridsize, startnum)
            xtags = list(dataset._axes.keys())
            axes.plot(dataset._axes[xtags[0]], dataset._data, label=name)
            axes.grid(True)
            axes.legend(loc=0)
            startnum += 1
        target.canvas.draw()
