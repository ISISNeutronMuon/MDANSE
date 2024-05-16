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

from matplotlib.pyplot import style as mpl_style
from matplotlib import colors

from MDANSE.Framework.Units import measure
from MDANSE.Core.SubclassFactory import SubclassFactory

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Plotter(metaclass=SubclassFactory):

    def __init__(self) -> None:
        self._figure = None

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
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        axes = target.add_subplot(111)
        try:
            matplotlib_style = colours["style"]
        except:
            pass
        else:
            if matplotlib_style is not None:
                mpl_style.use(matplotlib_style)
        try:
            bkg_col = colours["background"]
        except:
            pass
        else:
            if bkg_col is not None:
                target.set_facecolor(bkg_col)
                axes.set_facecolor(bkg_col)
        try:
            col_seq = colours["curves"]
        except:
            pass
        else:
            if col_seq is not None:
                axes.set_prop_cycle("color", col_seq)
        xaxis_unit = plotting_context._current_axis[0]
        for name, dataset in plotting_context._datasets.items():
            xtags = list(dataset._axes.keys())
            conversion_factor = measure(
                1.0, dataset._axes_units[xtags[0]], equivalent=True
            ).toval(xaxis_unit)
            axes.plot(
                dataset._axes[xtags[0]] * conversion_factor, dataset._data, label=name
            )
        axes.set_xlabel(xaxis_unit)
        axes.grid(True)
        axes.legend(loc=0)
        target.canvas.draw()
