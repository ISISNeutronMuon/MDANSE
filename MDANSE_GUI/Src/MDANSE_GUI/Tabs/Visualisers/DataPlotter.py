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

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableView,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from qtpy.QtCore import Slot, Signal

from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset


class DataPlotter(QWidget):
    """This part of the interface will show the selection of datasets
    created by the user, and allow the creation of a plot."""

    error = Signal(str)
    data_for_plotting = Signal(object)
    data_for_new_plot = Signal(object)
    create_new_plot = Signal(str)
    create_new_text = Signal(str)

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
            ("New Data View (Text)", self.new_text),
        ]
        for name, function in buttons:
            button = QPushButton(name, button_bar)
            button_layout.addWidget(button)
            if function is not None:
                button.clicked.connect(function)
        self._model = None

    @Slot(object)
    def add_dataset(self, dataset: SingleDataset):
        if self._model is None:
            self._model = PlottingContext(unit_lookup=self._unit_lookup)
            self._selection_viewer.setModel(self._model)
        self._model.add_dataset(dataset)
        self._selection_viewer.resizeColumnsToContents()
        for col_num in range(4, 8):
            self._selection_viewer.hideColumn(col_num)

    @Slot()
    def new_plot(self):
        self.create_new_plot.emit("")
        group = self._settings.group("dialogs")
        try:
            show_it = group.get("new_plot")
        except KeyError:
            show_it = group.get_default("dialogs", "new_plot")
        if show_it != "False":
            plot_added_box = QMessageBox.information(
                self,
                "Plot created",
                "A new plot has been created in the next tab (called 'Plot Holder').\n"
                "Should this message be shown every time this happens?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if plot_added_box == QMessageBox.StandardButton.No:
                group = self._settings.group("dialogs")
                group.set("new_plot", "False")

    @Slot()
    def new_text(self):
        self.create_new_text.emit("Text view")
        group = self._settings.group("dialogs")
        try:
            show_it = group.get("new_text")
        except KeyError:
            show_it = group.get_default("dialogs", "new_text")
        if show_it != "False":
            plot_added_box = QMessageBox.information(
                self,
                "Plot created",
                "A new text view has been created in the next tab (called 'Plot Holder').\n"
                "Should this message be shown every time this happens?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if plot_added_box == QMessageBox.StandardButton.No:
                group = self._settings.group("dialogs")
                group.set("new_text", "False")

    @Slot()
    def plot_data(self):
        if self._model is not None:
            if len(self._model.datasets()) == 0:
                return
            self.data_for_plotting.emit(self._model)
            group = self._settings.group("dialogs")
            try:
                show_it = group.get("data_plotted")
            except KeyError:
                show_it = group.get_default("dialogs", "data_plotted")
            if show_it != "False":
                data_plotted_box = QMessageBox.information(
                    self,
                    "Datasets plotted!",
                    "Your results have been plotted in the currently active plot in the next tab (called 'Plot Holder').\n"
                    "Should this message be shown every time this happens?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes,
                )
                if data_plotted_box == QMessageBox.StandardButton.No:
                    group = self._settings.group("dialogs")
                    group.set("data_plotted", "False")

    @Slot(object)
    def accept_data(self, data_set):
        LOG.info(f"Received {data_set}")
        dataset = SingleDataset(data_set[0], data_set[1])
        self.add_dataset(dataset)

    @Slot()
    def clear(self):
        if self._model is None:
            return
        self._model.clear()
        LOG.info(f"Cleared the plot")
