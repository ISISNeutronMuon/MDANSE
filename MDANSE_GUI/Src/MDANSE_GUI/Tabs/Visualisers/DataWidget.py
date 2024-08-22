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

if TYPE_CHECKING:
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext

import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from qtpy.QtCore import Slot, Signal, Qt

from MDANSE.MLogging import LOG

from MDANSE_GUI.Widgets.RestrictedSlider import RestrictedSlider
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter


class DataWidget(QWidget):

    change_slider_labels = Signal(object)
    change_slider_limits = Signal(object)
    reset_slider_values = Signal(bool)
    change_slider_coupling = Signal(bool)

    def __init__(self, *args, colours=None, settings=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._sliderpack = None
        self._plotting_context = None
        self._colours = colours
        self._settings = settings
        self._slider_max = 100
        self.make_canvas()
        # self.set_plotter("Text")

    def set_context(self, new_context: "PlottingContext"):
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        try:
            self._plotter = Plotter.create(plotter_option)
        except:
            self._plotter = Plotter()
        self._plotter._settings = self._settings
        self.plot_data()

    @Slot(object)
    def slider_change(self, new_values: object):
        self._plotter.handle_slider(new_values)

    @Slot(bool)
    def set_slider_values(self, reset_needed: bool):
        if reset_needed and self._sliderpack is not None:
            values = self._plotter._initial_values
            self._sliderpack.set_values(values)

    def available_plotters(self) -> List[str]:
        return [str(x) for x in Plotter.indirect_subclasses()]

    def plot_data(self, update_only=False):
        if self._plotter is None:
            LOG.info("No plotter present in PlotWidget.")
            return
        if self._plotting_context is None:
            return
        self._plotter.plot(
            self._plotting_context,
            self._figure,
            colours=self._colours,
            update_only=update_only,
            toolbar=self._toolbar,
        )

    def make_canvas(self):
        """Creates a matplotlib figure for plotting

        Parameters
        ----------
        width : float, optional
            Figure width in inches, by default 12.0
        height : float, optional
            Figure height in inches, by default 9.0
        dpi : int, optional
            Figure resolution in dots per inch, by default 100

        Returns
        -------
        QWidget
            a widget containing both the figure and a toolbar below
        """
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self._figure = QTextBrowser(self)
        layout.addWidget(self._figure)
