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

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlottingContext import (
    PlottingContext,
    SingleDataset,
)

WIDGET_DESCRIPTIONS = {"DataWidget": "text view", "PlotWidget": "plot view"}


class DataPlotter(QWidget):
    """Part of PlotCreator which sends datasets to the plotter.

    This part of the interface will show the selection of datasets
    created by the user, and allow the creation of a plot.
    """

    error = Signal(str)
    data_for_plotting = Signal(object)
    data_for_new_plot = Signal(object)
    create_new_plot = Signal(str)
    create_new_text = Signal(str)

    def __init__(self, *args, unit_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tab_index, self.tab_count = 0, 1
        self.tab_name = "Preview"
        self.dataset_count = 0
        self.plotter_type = "PlotWidget"
        self._unit_lookup = unit_lookup
        layout = QVBoxLayout(self)
        control_bar = QWidget(self)
        lower_bar_layout = QHBoxLayout(control_bar)
        selection_bar = QWidget(self)
        upper_bar_layout = QHBoxLayout(selection_bar)
        self._selection_viewer = QTableView(self)
        button_bar1, button_bar2 = self.create_buttons()
        plotter_preview = self.create_preview()
        layout.addWidget(selection_bar)
        layout.addWidget(control_bar)
        upper_bar_layout.addWidget(button_bar2)
        upper_bar_layout.addWidget(self._selection_viewer)
        lower_bar_layout.addWidget(button_bar1)
        lower_bar_layout.addWidget(plotter_preview)
        self._model = PlottingContext(
            unit_lookup=self._unit_lookup,
        )
        self._selection_viewer.setModel(self._model)
        self.hide_columns()

    def create_buttons(self) -> QWidget:
        self._plotting_button_reference = None
        button_groups = {
            "Empty plot creation": [
                ("New empty plot", self.new_plot),
                ("New empty text view", self.new_text),
            ],
            "Current data selection": [
                ("Send data to plotter", self.plot_data),
                ("Clear data selection", self.clear),
            ],
        }
        bars = []
        for group_name, buttons in button_groups.items():
            button_bar = QWidget(self)
            button_layout = QVBoxLayout(button_bar)
            subgroup = QGroupBox(group_name, button_bar)
            sublayout = QVBoxLayout(subgroup)
            for name, function in buttons:
                button = QPushButton(name, button_bar)
                sublayout.addWidget(button)
                if function is not None:
                    button.clicked.connect(function)
                if name == "Send data to plotter":
                    self._plotting_button_reference = button
            button_layout.addWidget(subgroup)
            bars.append(button_bar)
        return bars

    def create_preview(self) -> QWidget:
        previewer = QWidget(self)
        previewer_layout = QVBoxLayout(previewer)
        self.target_label = QLabel("Target plot in next tab.")
        self.target_label.setWordWrap(True)
        previewer_layout.addWidget(self.target_label)
        self.info_label = QLabel(
            f"Contents of the currently selected {self.plotter_type} in the next tab:"
        )
        previewer_layout.addWidget(self.info_label)
        self.preview_table = QTableView(previewer)
        previewer_layout.addWidget(self.preview_table)
        self.update_target_plot_label()
        return previewer

    def update_target_plot_label(self):
        output_widget = WIDGET_DESCRIPTIONS.get(self.plotter_type, "data visualiser")
        self.info_label.setText(
            f"Contents of the currently selected {output_widget} in the next tab:"
        )
        self.target_label.setText(
            "Datasets listed above will be sent to the <b>Plot Holder</b> tab.<br>"
            f"They will appear in '{self.tab_name}' in the Plot Holder tab.<br>"
            f"'{self.tab_name}' is a {output_widget}, "
            f"currently containing {self.dataset_count} datasets."
        )
        self._plotting_button_reference.setText(f"Send data to {output_widget}")
        for col_num in range(4, 10):
            self.preview_table.hideColumn(col_num)
        self.preview_table.resizeColumnsToContents()

    @Slot(int)
    def new_target_plot_index(self, new_index: int):
        self.tab_index = new_index
        self.update_target_plot_label()

    @Slot(str)
    def new_target_plot_name(self, new_name: str):
        self.tab_name = new_name
        self.update_target_plot_label()

    @Slot(int)
    def new_target_plot_count(self, new_count: int):
        self.tab_count = new_count
        self.update_target_plot_label()

    @Slot(int)
    def new_dataset_count_in_target(self, new_dataset_count: int):
        self.dataset_count = new_dataset_count
        self.update_target_plot_label()

    @Slot(str)
    def new_plot_widget_type(self, new_plot_widget_type: str):
        self.plotter_type = new_plot_widget_type
        self.update_target_plot_label()

    @Slot(object)
    def add_dataset(self, dataset: SingleDataset):
        """Append a dataset to the current model."""
        if not dataset._valid:
            return
        self._model.add_dataset(dataset)
        self._selection_viewer.resizeColumnsToContents()
        self.hide_columns()

    def hide_columns(self):
        """Only show the first four columns of plotting_column_labels."""
        for col_num in range(4, 10):
            self._selection_viewer.hideColumn(col_num)

    @Slot()
    def new_plot(self):
        """Trigger the creation of a new plot in the plotting tab."""
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
        """Trigger the creation of a new text view in the plotting tab."""
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
        """Send the data from the internal model to the plotting tab."""
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
        """Append the incoming data to the inner model."""
        LOG.info(f"Received {data_set}")
        dataset = SingleDataset(data_set[0], data_set[1])
        self.add_dataset(dataset)

    @Slot()
    def clear(self):
        """Remove all the entries from the model."""
        if self._model is None:
            return
        self._model.clear()
        for col_num in range(4, 10):
            self._selection_viewer.hideColumn(col_num)
        LOG.debug("Cleared the plot")
