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

from qtpy.QtWidgets import QVBoxLayout, QTabWidget
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.Tabs.Visualisers.PlotWidget import PlotWidget
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class PlotHolder(QTabWidget):
    """This is the top-layer widget which will host any number of
    PlotWidgets.
    """

    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self._context = {}
        self._plotter = {}
        self._current_id = -1
        self.setLayout(layout)
        self._current_id = self.new_plot("preview")

    @Slot(str)
    def new_plot(self, tab_name: str) -> int:
        try:
            preferred_units = self._session._units
        except:
            preferred_units = None
        plotting_context = PlottingContext(unit_preference=preferred_units)
        plotter = PlotWidget(self)
        plotter.set_context(plotting_context)
        tab_id = self.addTab(plotter, tab_name)
        self._context[tab_id] = plotting_context
        self._plotter[tab_id] = plotter
        return tab_id

    @property
    def model(self):
        tab_id = self.currentIndex()
        return self._context[tab_id]

    @property
    def plotter(self):
        tab_id = self.currentIndex()
        return self._plotter[tab_id]

    @Slot(object)
    def update_plot_details(self, input):
        """This will change the line colour, thickness, etc.
        At the moment it doesn't do anything."""
