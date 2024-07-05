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

from qtpy.QtWidgets import QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset


class DataPlotter(QWidget):
    """This part of the interface will show the selection of datasets
    created by the user, and allow the creation of a plot."""

    error = Signal(str)
    data_for_plotting = Signal(object)
    data_for_new_plot = Signal(object)
    create_new_plot = Signal(str)

    def __init__(self, *args, unit_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._unit_lookup = unit_lookup
        layout = QVBoxLayout(self)
        button_bar = QWidget(self)
        button_layout = QHBoxLayout(button_bar)
        self._selection_viewer = QTableView(self)
        layout.addWidget(self._selection_viewer)
        layout.addWidget(button_bar)
        buttons = [
            ("Plot Data", self.plot_data),
            ("Clear", self.clear),
            ("New Plot", self.new_plot),
        ]
        for name, function in buttons:
            button = QPushButton(name, button_bar)
            button_layout.addWidget(button)
            if function is not None:
                button.clicked.connect(function)
        self._model = None

    @Slot(object)
    def add_dataset(self, dataset: SingleDataset):
        unit_group = self._settings.group("units")
        if self._model is None:
            try:
                preferred_units = unit_group.as_dict()
            except:
                preferred_units = None
            self._model = PlottingContext(unit_lookup=self._unit_lookup)
            self._selection_viewer.setModel(self._model)
        self._model.add_dataset(dataset)
        self._selection_viewer.resizeColumnsToContents()
        self._selection_viewer.hideColumn(4)

    @Slot()
    def new_plot(self):
        self.create_new_plot.emit("")

    @Slot()
    def plot_data(self):
        if self._model is not None:
            self.data_for_plotting.emit(self._model)

    @Slot(object)
    def accept_data(self, data_set):
        print(f"Received {data_set}")
        dataset = SingleDataset(data_set[0], data_set[1])
        self.add_dataset(dataset)

    @Slot()
    def clear(self):
        if self._model is None:
            return
        self._model.clear()
        print(f"Cleared the plot")
