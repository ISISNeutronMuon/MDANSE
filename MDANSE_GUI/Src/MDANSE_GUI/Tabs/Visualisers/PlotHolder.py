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
from __future__ import annotations

import traceback

from more_itertools import first_true
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QTabBar, QTabWidget, QVBoxLayout

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext
from MDANSE_GUI.Tabs.Visualisers.DataWidget import DataWidget
from MDANSE_GUI.Tabs.Visualisers.PlotWidget import PlotWidget


class PlotHolder(QTabWidget):
    """This is the top-layer widget which will host any number of
    PlotWidgets.
    """

    error = Signal(str)
    new_entry = Signal()

    def __init__(self, *args, unit_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._settings = None
        self._last_number = 1
        layout = QVBoxLayout(self)
        self._context = []
        self._plotter = []
        self._unit_lookup = unit_lookup
        self._current_id = -1
        self.setLayout(layout)
        self._current_id = self.new_plot("Preview")
        self._protected_id = int(self._current_id)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.clean_up_closed_tab)
        # remove the close button on the protected tab
        tabbar = self.tabBar()
        close_button = tabbar.tabButton(
            self._protected_id, QTabBar.ButtonPosition.RightSide
        )
        close_button.deleteLater()
        tabbar.setTabButton(self._protected_id, QTabBar.ButtonPosition.RightSide, None)

    @Slot(str)
    def new_plot(self, tab_name: str) -> int:
        if not tab_name:
            tab_name = f"New plot {self._last_number}"
            self._last_number += 1
        plotting_context = PlottingContext(
            unit_lookup=self._unit_lookup,
        )
        plotting_context.needs_an_update.connect(self.update_plot)
        plotter = PlotWidget(self)
        plotter.set_context(plotting_context)
        tab_id = self.addTab(plotter, tab_name)
        LOG.info(f"PlotHolder created tab: {tab_id}")
        self._context.append(plotting_context)
        self._plotter.append(plotter)
        self.setCurrentIndex(tab_id)
        self.new_entry.emit()
        return tab_id

    @Slot(str)
    def new_text(self, ignored_name: str) -> int:
        tab_name = f"New text view {self._last_number}"
        self._last_number += 1
        plotting_context = PlottingContext(unit_lookup=self._unit_lookup)
        plotting_context.needs_an_update.connect(self.update_plot)
        plotter = DataWidget(self)
        plotter.set_context(plotting_context)
        tab_id = self.addTab(plotter, tab_name)
        LOG.info(f"PlotHolder created tab: {tab_id}")
        self._context.append(plotting_context)
        self._plotter.append(plotter)
        self.setCurrentIndex(tab_id)
        self.new_entry.emit()
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
            pc = self._context[tab_id]
        except KeyError:
            LOG.error(f"Plotting context is missing for tab {tab_id}")
            LOG.error(self._context)
        else:
            pc._unit_lookup = self._unit_lookup
            return pc

    @property
    def plotter(self):
        tab_id = self.currentIndex()
        try:
            return self._plotter[tab_id]
        except KeyError:
            LOG.error(f"PlotWidget is missing for tab {tab_id}")
            LOG.error(self._plotter)

    @Slot()
    def update_plots(self):
        """Update all plots.

        This is typically needed if the global matplotlib settings have been changed."""
        for plotter in self._plotter:
            try:
                plotter.plot_data(update_only=True)
            except Exception:
                LOG.error("Plotting failed: %s", traceback.format_exc())
                plotter.plot_blank()

    @Slot("quint64")
    def update_plot(self, plot_number: int):
        """Update the plot in a specific PlotWidget.

        Updates the plot only in the PlotWidget matching the object ID of the
        PlottingContext which requested the update.

        Parameters
        ----------
        plot_number : int
            Object id of the PlottingContext in which the settings got changed.
        """
        plotter = first_true(
            self._plotter, pred=lambda plot: plot.unique_id == plot_number
        )
        if plotter is None:
            return
        try:
            plotter.plot_data(update_only=True)
        except Exception:
            LOG.error("Plotting failed: %s", traceback.format_exc())
            plotter.plot_blank()
