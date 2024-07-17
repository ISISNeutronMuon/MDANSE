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

from MDANSE.MLogging import LOG
from MDANSE.Core.SubclassFactory import SubclassFactory

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Plotter(metaclass=SubclassFactory):

    def __init__(self) -> None:
        self._figure = None
        self._current_colours = []
        self._axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None

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

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def sliders_coupled(self) -> bool:
        return False

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
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def apply_settings(self, plotting_context: "PlottingContext", colours=None):
        if colours is not None:
            self._current_colours = colours
        if plotting_context.set_axes() is None:
            LOG.error("Axis check failed.")
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

    def handle_slider(self, new_value: List[float]):
        self._slider_values = new_value

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "Figure" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self.get_mpl_colors()
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context, colours)
