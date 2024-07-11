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
from qtpy.QtWidgets import QVBoxLayout, QTabWidget
from qtpy.QtCore import Slot, Signal

from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Visualisers.PlotWidget import PlotWidget
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class PlotHolder(QTabWidget):
    """This is the top-layer widget which will host any number of
    PlotWidgets.
    """

    error = Signal(str)

    def __init__(self, *args, session=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._session = session
        self._last_number = 1
        layout = QVBoxLayout(self)
        self._context = []
        self._plotter = []
        self._current_id = -1
        self.setLayout(layout)
        self._current_id = self.new_plot("Preview")
        self._protected_id = int(self._current_id)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.clean_up_closed_tab)

    @Slot(str)
    def new_plot(self, tab_name: str) -> int:
        try:
            preferred_units = self._session._units
        except:
            preferred_units = None
        if not tab_name:
            tab_name = f"New plot {self._last_number}"
            self._last_number += 1
        plotting_context = PlottingContext(unit_preference=preferred_units)
        self._session.new_units.connect(plotting_context.accept_units)
        self._session.new_cmap.connect(plotting_context.accept_cmap)
        plotting_context.needs_an_update.connect(self.update_plots)
        plotter = PlotWidget(self)
        plotter.set_context(plotting_context)
        tab_id = self.addTab(plotter, tab_name)
        LOG.info(f"PlotHolder created tab: {tab_id}")
        self._context.append(plotting_context)
        self._plotter.append(plotter)
        self.setCurrentIndex(tab_id)
        return tab_id

    @Slot(int)
    def clean_up_closed_tab(self, tab_id: int):
        if tab_id == self._protected_id:
            return
        valid_id_values = [int(idnum) for idnum in range(len(self._plotter))]
        if tab_id in valid_id_values:
            valid_id_values.pop(valid_id_values.index(tab_id))
        if tab_id < len(self._context):
            self._context.pop(tab_id)
        if tab_id < len(self._plotter):
            self._plotter.pop(tab_id)
        if self._current_id == tab_id:
            if len(valid_id_values) > 0:
                self._current_id = valid_id_values[0]
                self.setCurrentIndex(self._current_id)
        self.removeTab(tab_id)

    @property
    def model(self):
        tab_id = self.currentIndex()
        try:
            return self._context[tab_id]
        except KeyError:
            LOG.error(f"Plotting context is missing for tab {tab_id}")
            LOG.error(self._context)

    @property
    def plotter(self):
        tab_id = self.currentIndex()
        try:
            return self._plotter[tab_id]
        except KeyError:
            LOG.error(f"PlotWidget is missing for tab {tab_id}")
            LOG.error(self._plotter)

    @Slot(object)
    def update_plot_details(self, input):
        """This will change the line colour, thickness, etc.
        At the moment it doesn't do anything."""

    @Slot()
    def update_plots(self):
        """This will change the line colour, thickness, etc.
        At the moment it doesn't do anything."""
        for plotter in self._plotter:
            plotter.plot_data(update_only=True)
