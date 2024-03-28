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

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

from MDANSE_GUI.Plotter.views.table_views import QTableViewWithoutRightClick
from MDANSE_GUI.Plotter.widgets.range_slider import RangeSlider


class InspectDataDialog(QtWidgets.QDialog):
    def __init__(self, dataset_info, *args, **kwargs):
        """Constructor.

        Args:
            dataset_info (dict): the information about the dataset to display
        """
        super(InspectDataDialog, self).__init__(*args, **kwargs)

        self._dataset_info = dataset_info

        self._build()

        self.setWindowTitle(dataset_info["variable"])

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        self._data_tableview = QTableViewWithoutRightClick()
        self._data_tableview.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._data_tableview.customContextMenuRequested.connect(
            self.on_open_contextual_menu
        )
        main_layout.addWidget(self._data_tableview)

        if self._dataset_info["dimension"] > 1:
            grid_layout = QtWidgets.QGridLayout()

            grid_layout.addWidget(QtWidgets.QLabel("Row"), 0, 1)
            grid_layout.addWidget(QtWidgets.QLabel("Col"), 0, 2)

            self._row_button_group = QtWidgets.QButtonGroup()
            self._row_button_group.setExclusive(True)

            self._col_button_group = QtWidgets.QButtonGroup()
            self._col_button_group.setExclusive(True)

            self._lines = []
            for i, s in enumerate(self._dataset_info["shape"]):
                axis_label = QtWidgets.QLabel(f"Axis {i}")
                grid_layout.addWidget(axis_label, i + 1, 0)

                row_radio_button = QtWidgets.QRadioButton("")
                grid_layout.addWidget(row_radio_button, i + 1, 1)
                self._row_button_group.addButton(row_radio_button)
                self._row_button_group.setId(row_radio_button, i)

                col_radio_button = QtWidgets.QRadioButton("")
                grid_layout.addWidget(col_radio_button, i + 1, 2)
                self._col_button_group.addButton(col_radio_button)
                self._col_button_group.setId(col_radio_button, i)

                slice_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
                slice_slider.setMinimum(0)
                slice_slider.setMaximum(s - 1)
                grid_layout.addWidget(slice_slider, i + 1, 3)

                slice_spinbox = QtWidgets.QSpinBox()
                slice_spinbox.setMinimum(0)
                slice_spinbox.setMaximum(s - 1)
                grid_layout.addWidget(slice_spinbox, i + 1, 4)

                sum_along_dimension_checkbox = QtWidgets.QCheckBox("sum")
                grid_layout.addWidget(sum_along_dimension_checkbox, i + 1, 5)

                range_label = QtWidgets.QLabel("Range")
                range_label.setDisabled(True)
                grid_layout.addWidget(range_label, i + 1, 6)

                sum_range_slider = RangeSlider(QtCore.Qt.Orientation.Horizontal)
                sum_range_slider.setMinimum(0)
                sum_range_slider.setMaximum(s - 1)
                sum_range_slider.setLow(0)
                sum_range_slider.setHigh(s - 1)
                sum_range_slider.setDisabled(True)
                grid_layout.addWidget(sum_range_slider, i + 1, 7)

                min_range_spinbox = QtWidgets.QSpinBox()
                min_range_spinbox.setMinimum(0)
                min_range_spinbox.setMaximum(s - 1)
                min_range_spinbox.setValue(0)
                min_range_spinbox.setDisabled(True)
                grid_layout.addWidget(min_range_spinbox, i + 1, 8)

                max_range_spinbox = QtWidgets.QSpinBox()
                max_range_spinbox.setMinimum(0)
                max_range_spinbox.setMaximum(s - 1)
                max_range_spinbox.setValue(s - 1)
                max_range_spinbox.setDisabled(True)
                grid_layout.addWidget(max_range_spinbox, i + 1, 9)

                slice_slider.sliderReleased.connect(
                    lambda index=i: self.on_select_slice_by_slider(index)
                )
                slice_spinbox.valueChanged.connect(
                    lambda value, index=i: self.on_select_slice_by_spinbox(value, index)
                )
                sum_along_dimension_checkbox.stateChanged.connect(
                    lambda state, index=i: self.on_sum_along_axis(state, index)
                )
                sum_range_slider.slider_moved.connect(
                    lambda min, max, index=i: self.on_select_sum_range_by_slider(
                        min, max, index
                    )
                )
                min_range_spinbox.valueChanged.connect(
                    lambda value, index=i: self.on_select_min_range_by_spinbox(
                        value, index
                    )
                )
                max_range_spinbox.valueChanged.connect(
                    lambda value, index=i: self.on_select_max_range_by_spinbox(
                        value, index
                    )
                )

                self._lines.append(
                    [
                        axis_label,
                        row_radio_button,
                        col_radio_button,
                        slice_slider,
                        slice_spinbox,
                        sum_along_dimension_checkbox,
                        range_label,
                        sum_range_slider,
                        min_range_spinbox,
                        max_range_spinbox,
                    ]
                )

            self.set_dimension(0, 1)

            self._row_button_group.buttonClicked.connect(self.on_select_row)
            self._col_button_group.buttonClicked.connect(self.on_select_col)

            main_layout.addLayout(grid_layout)

        else:
            self.update()

        self.setLayout(main_layout)

    def on_copy_to_clipboard(self):
        """Callback called when some data has been copied to the clipboard."""
        model = self._data_tableview.model()
        selection_model = self._data_tableview.selectionModel()

        selected_columns = set()
        for data_range in selection_model.selection():
            for i in range(data_range.top(), data_range.bottom() + 1):
                for j in range(data_range.left(), data_range.right() + 1):
                    selected_columns.add(j)
        selected_columns = sorted(selected_columns)

        copied_data = []
        for data_range in selection_model.selection():
            for i in range(data_range.top(), data_range.bottom() + 1):
                line = []
                for j in selected_columns:
                    if j in range(data_range.left(), data_range.right() + 1):
                        value = model.data(
                            model.index(i, j), QtCore.Qt.ItemDataRole.DisplayRole
                        )
                    else:
                        value = ""
                    line.append(value)
                line = ",".join(line)
                copied_data.append(line)

        copied_data = "\n".join(copied_data)

        QtWidgets.QApplication.clipboard().setText(copied_data)

    def on_open_contextual_menu(self, point):
        """Callback called when the contextual menu is opened by right-clicking on the data.

        Args:
            point (qtpy.QtCore.QPoint): the point of click
        """
        menu = QtWidgets.QMenu(self)
        copy_to_clipboard_action = menu.addAction("Copy to clipboard")
        copy_to_clipboard_action.triggered.connect(self.on_copy_to_clipboard)
        menu.exec(self._data_tableview.mapToGlobal(point))

    def on_select_col(self, states):
        """Callback called when the index of the col buttongroup is changed.

        Args:
            states (list): the states of the button group
        """
        row_id = self._row_button_group.checkedId()
        col_id = self._col_button_group.checkedId()
        if row_id == col_id:
            self._lines[self._current_col][1].setChecked(True)
            self._current_row = self._current_col
        else:
            self._lines[col_id][3].setDisabled(True)
            self._lines[self._current_col][3].setDisabled(
                self._lines[self._current_col][5].isChecked()
            )
            self._lines[col_id][4].setDisabled(True)
            self._lines[self._current_col][4].setDisabled(
                self._lines[self._current_col][5].isChecked()
            )
            self._lines[col_id][5].setDisabled(True)
            self._lines[self._current_col][5].setDisabled(False)
            self._lines[col_id][6].setDisabled(True)
            self._lines[self._current_col][6].setDisabled(
                not self._lines[self._current_col][5].isChecked()
            )
            self._lines[col_id][7].setDisabled(True)
            self._lines[self._current_col][7].setDisabled(
                not self._lines[self._current_col][5].isChecked()
            )
            self._lines[col_id][8].setDisabled(True)
            self._lines[self._current_col][8].setDisabled(
                not self._lines[self._current_col][5].isChecked()
            )
            self._lines[col_id][9].setDisabled(True)
            self._lines[self._current_col][9].setDisabled(
                not self._lines[self._current_col][5].isChecked()
            )

        self._current_col = col_id

        self.set_dimension(self._current_row, self._current_col)

    def on_select_min_range_by_spinbox(self, min, index):
        """Callback called when the value of the minimum of the sum range spinbox is changed for a given axis.

        Args:
            min (int): the minimum value
            index (int): the index of the axis
        """
        self._lines[index][7].setLow(min)
        self._lines[index][9].setMinimum(min + 1)
        self.update()

    def on_select_max_range_by_spinbox(self, max, index):
        """Callback called when the value of the maximum of the sum range spinbox is changed for a given axis.

        Args:
            max (int): the maximum value
            index (int): the index of the axis
        """
        self._lines[index][7].setHigh(max)
        self._lines[index][8].setMaximum(max - 1)
        self.update()

    def on_select_row(self, states):
        """Callback called when the index of the row buttongroup is changed.

        Args:
            states (list): the states of the button group
        """
        row_id = self._row_button_group.checkedId()
        col_id = self._col_button_group.checkedId()
        if row_id == col_id:
            self._lines[self._current_row][2].setChecked(True)
            self._current_col = self._current_row
        else:
            self._lines[row_id][3].setDisabled(True)
            self._lines[self._current_row][3].setDisabled(
                self._lines[self._current_row][5].isChecked()
            )
            self._lines[row_id][4].setDisabled(True)
            self._lines[self._current_row][4].setDisabled(
                self._lines[self._current_row][5].isChecked()
            )
            self._lines[row_id][5].setDisabled(True)
            self._lines[self._current_row][5].setDisabled(False)
            self._lines[row_id][6].setDisabled(True)
            self._lines[self._current_row][6].setDisabled(
                not self._lines[self._current_row][5].isChecked()
            )
            self._lines[row_id][7].setDisabled(True)
            self._lines[self._current_row][7].setDisabled(
                not self._lines[self._current_row][5].isChecked()
            )
            self._lines[row_id][8].setDisabled(True)
            self._lines[self._current_row][8].setDisabled(
                not self._lines[self._current_row][5].isChecked()
            )
            self._lines[row_id][9].setDisabled(True)
            self._lines[self._current_row][9].setDisabled(
                not self._lines[self._current_row][5].isChecked()
            )

        self._current_row = row_id

        self.set_dimension(self._current_row, self._current_col)

    def on_select_slice_by_slider(self, index):
        """Callback called when the selected slice slider value is changed for a given axis.

        Args:
            index (int): the index of the axis
        """
        value = self._lines[index][3].value()
        self._lines[index][4].blockSignals(True)
        self._lines[index][4].setValue(value)
        self._lines[index][4].blockSignals(False)
        self.update()

    def on_select_slice_by_spinbox(self, value, index):
        """Callback called when the selected slice spinbox value is changed for a given axis.

        Args:
            value (int): the selected slice
            index (int): the index of the axis
        """
        self._lines[index][3].blockSignals(True)
        self._lines[index][3].setValue(value)
        self._lines[index][3].blockSignals(False)
        self.update()

    def on_select_sum_range_by_slider(self, min, max, index):
        """Callback called when the sum range value is changed through the corresponding slider for a given axis.

        Args:
            min (int): the minimum value
            max (int): the maximum value
            index (int): the index of the axis
        """
        self._lines[index][8].setMaximum(max - 1)
        self._lines[index][8].blockSignals(True)
        self._lines[index][8].setValue(min)
        self._lines[index][8].blockSignals(False)
        self._lines[index][9].setMinimum(min + 1)
        self._lines[index][9].blockSignals(True)
        self._lines[index][9].setValue(max)
        self._lines[index][9].blockSignals(False)
        self.update()

    def on_sum_along_axis(self, state, index):
        """Callback called when the sum along axis checkbox toggle state is changed for a given axis.

        Args:
            state (bool): the sum along axis checkbox toggle state
            index (int): the index of the axis
        """
        self._lines[index][3].setDisabled(state)
        self._lines[index][4].setDisabled(state)

        self._lines[index][6].setDisabled(not state)
        self._lines[index][7].setDisabled(not state)
        self._lines[index][8].setDisabled(not state)
        self._lines[index][9].setDisabled(not state)
        self.update()

    def set_dimension(self, row, col):
        """Set the selected row and column of the data to display.

        Args:
            row (int): the row to select
            col (int): the col to select
        """
        self._current_row = row
        self._current_col = col
        self._lines[row][1].setChecked(True)
        self._lines[col][2].setChecked(True)

        self._lines[self._current_row][3].setDisabled(True)
        self._lines[self._current_col][3].setDisabled(True)

        self._lines[self._current_row][4].setDisabled(True)
        self._lines[self._current_col][4].setDisabled(True)

        self._lines[self._current_row][5].setDisabled(True)
        self._lines[self._current_col][5].setDisabled(True)

        self._lines[self._current_row][6].setDisabled(True)
        self._lines[self._current_col][6].setDisabled(True)

        self._lines[self._current_row][7].setDisabled(True)
        self._lines[self._current_col][7].setDisabled(True)

        self._lines[self._current_row][8].setDisabled(True)
        self._lines[self._current_col][8].setDisabled(True)

        self.update()

    def update(self):
        """ """
        model = QtGui.QStandardItemModel()

        if self._dataset_info["dimension"] == 1:
            for v in self._dataset_info["data"]:
                model.appendRow(QtGui.QStandardItem(str(v)))
        else:
            data = self._dataset_info["data"]

            # This will setup the slice of the nd data in order to reduce it to a 2D data that can be display on the table
            sli = []
            # This will store the dimensions for which a sum has to be performed if any
            summed_axis = []
            for i in range(self._dataset_info["dimension"]):
                # For the selected row and column take the complete slice
                if (i == self._current_row) or (i == self._current_col):
                    sli.append(slice(None))
                else:
                    # Case where a sum is performed for dimension i: create a slice out of the min and max values of the corresponding spinboxes
                    if self._lines[i][5].isChecked():
                        f = self._lines[i][8].value()
                        l = self._lines[i][9].value()
                        s = slice(f, l + 1, 1)
                        sli.append(s)
                        summed_axis.append(i)
                    else:
                        sli.append(self._lines[i][4].value())

            data = data[tuple(sli)]
            # Sum the data if necessary. summed_axis can be empty - in such case no sum is performed
            data = np.sum(data, axis=tuple(summed_axis))
            # Transpose the data if necessary
            if self._current_row > self._current_col:
                data = data.T
            for row in data:
                model.appendRow([QtGui.QStandardItem(str(c)) for c in row])

        self._data_tableview.setModel(model)
