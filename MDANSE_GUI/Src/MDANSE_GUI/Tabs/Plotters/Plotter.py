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

from matplotlib.pyplot import style as mpl_style
from matplotlib import rcParams

from MDANSE.Core.SubclassFactory import SubclassFactory

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Plotter(metaclass=SubclassFactory):

    def __init__(self) -> None:
        self._figure = None
        self._current_colours = []
        self._axes = []
        self._slider_value = 0.0

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> List[str]:
        return ["Slider 1", "Slider 2"]

    def get_mpl_colors(self):
        cycler = rcParams["axes.prop_cycle"]
        colours = cycler.by_key()["color"]
        self._current_colours = colours

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

    def apply_settings(self, plotting_context: "PlottingContext", colours=None):
        if colours is not None:
            self._current_colours = colours
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
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
                for axes in self._axes:
                    axes.set_facecolor(bkg_col)
        try:
            col_seq = colours["curves"]
        except:
            pass
        else:
            if col_seq is not None:
                for axes in self._axes:
                    axes.set_prop_cycle("color", col_seq)

    def handle_slider(self, new_value: float):
        self._slider_value = new_value

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
