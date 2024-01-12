# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     root file of Plotter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

from qtpy import QtCore, QtWidgets

from MDANSE_GUI.PyQtGUI.Plotter.widgets.range_slider import RangeSlider


class SliceViewerDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, parent):
        """Constructor.

        Args:
            plot_nd_model (Plotter.models.plot_nd_model.PlotNDModel): the ND data model
            parent (qtpy.QtWidgets.QWidget): the parent
        """
        super(SliceViewerDialog, self).__init__(parent)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.on_update()

        self.setWindowTitle("Slice viewer dialog")

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        grid_layout = QtWidgets.QGridLayout()

        self._x_axis_button_group = QtWidgets.QButtonGroup()
        self._x_axis_button_group.setExclusive(True)

        self._y_axis_button_group = QtWidgets.QButtonGroup()
        self._y_axis_button_group.setExclusive(True)

        grid_layout.addWidget(QtWidgets.QLabel("Axis"), 0, 0)
        grid_layout.addWidget(QtWidgets.QLabel("X"), 0, 1)
        grid_layout.addWidget(QtWidgets.QLabel("Y"), 0, 2)
        grid_layout.addWidget(QtWidgets.QLabel("Slices"), 0, 3)

        self._lines = []
        for i in range(self._plot_nd_model.get_n_dimensions()):
            axis_label = QtWidgets.QLabel()
            grid_layout.addWidget(axis_label, i + 1, 0)

            x_axis_radio_button = QtWidgets.QRadioButton("")
            grid_layout.addWidget(x_axis_radio_button, i + 1, 1)
            self._x_axis_button_group.addButton(x_axis_radio_button)
            self._x_axis_button_group.setId(x_axis_radio_button, i)

            y_axis_radio_button = QtWidgets.QRadioButton("")
            grid_layout.addWidget(y_axis_radio_button, i + 1, 2)
            self._y_axis_button_group.addButton(y_axis_radio_button)
            self._y_axis_button_group.setId(y_axis_radio_button, i)

            slice_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
            grid_layout.addWidget(slice_slider, i + 1, 3)

            slice_spinbox = QtWidgets.QSpinBox()
            grid_layout.addWidget(slice_spinbox, i + 1, 4)

            sum_along_dimension_checkbox = QtWidgets.QCheckBox("sum")
            grid_layout.addWidget(sum_along_dimension_checkbox, i + 1, 5)

            range_label = QtWidgets.QLabel("Range")
            range_label.setDisabled(True)
            grid_layout.addWidget(range_label, i + 1, 6)

            sum_range_slider = RangeSlider(QtCore.Qt.Orientation.Horizontal)
            sum_range_slider.setDisabled(True)
            grid_layout.addWidget(sum_range_slider, i + 1, 7)

            min_range_spinbox = QtWidgets.QSpinBox()
            min_range_spinbox.setDisabled(True)
            grid_layout.addWidget(min_range_spinbox, i + 1, 8)

            max_range_spinbox = QtWidgets.QSpinBox()
            max_range_spinbox.setDisabled(True)
            grid_layout.addWidget(max_range_spinbox, i + 1, 9)

            range_label = QtWidgets.QLabel()
            grid_layout.addWidget(range_label, i + 1, 10)

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
                lambda value, index=i: self.on_select_min_range_by_spinbox(value, index)
            )
            max_range_spinbox.valueChanged.connect(
                lambda value, index=i: self.on_select_max_range_by_spinbox(value, index)
            )

            self._lines.append(
                [
                    axis_label,
                    x_axis_radio_button,
                    y_axis_radio_button,
                    slice_slider,
                    slice_spinbox,
                    sum_along_dimension_checkbox,
                    range_label,
                    sum_range_slider,
                    min_range_spinbox,
                    max_range_spinbox,
                    range_label,
                ]
            )

        main_layout.addLayout(grid_layout)

        self.setLayout(main_layout)

        self._plot_nd_model.x_variable_updated.connect(self.on_x_variable_updated)
        self._plot_nd_model.y_variable_updated.connect(self.on_y_variable_updated)

        self._x_axis_button_group.buttonClicked.connect(self.on_select_x_axis)
        self._y_axis_button_group.buttonClicked.connect(self.on_select_y_axis)

    def _update_model(self):
        """Update the ND data model underlying the dialog."""
        x_axis_radiobuttons = [line[1] for line in self._lines]
        x_axis_idx = x_axis_radiobuttons.index(
            self._x_axis_button_group.checkedButton()
        )

        y_axis_radiobuttons = [line[2] for line in self._lines]
        y_axis_idx = y_axis_radiobuttons.index(
            self._y_axis_button_group.checkedButton()
        )

        slices = [None] * len(self._lines)
        slices[x_axis_idx] = slice(None)
        slices[y_axis_idx] = slice(None)
        summed_dimensions = [False] * len(self._lines)

        for i, line in enumerate(self._lines):
            if (i == x_axis_idx) or (i == y_axis_idx):
                continue
            if line[5].isEnabled() and line[5].isChecked():
                slices[i] = slice(line[7].low(), line[7].high() + 1, 1)
                summed_dimensions[i] = True
            else:
                slices[i] = slice(line[3].value(), line[3].value() + 1, 1)
                summed_dimensions[i] = False

        transpose = x_axis_idx > y_axis_idx

        self._plot_nd_model.update_model(
            list(zip(slices, summed_dimensions)), transpose
        )

    def _update_range_label(self, index, min, max):
        """Update the sum range label for a given axis.

        Args:
            index (int): the axis index
            min (int): the minimum value
            max (int): the maximum value
        """
        axis_current_data = self._plot_nd_model.get_axis_current_data()
        axis_current_units = self._plot_nd_model.get_axis_current_units()
        f = axis_current_data[index][min]
        t = axis_current_data[index][max]
        unit = axis_current_units[index]
        self._lines[index][10].setText(f"from {f} {unit} to {t} {unit}")

    def on_select_min_range_by_spinbox(self, min, index):
        """Callback called when the value of the minimum of the sum range spinbox is changed for a given axis.

        Args:
            min (int): the minimum value
            index (int): the index of the axis
        """
        self._lines[index][7].setLow(min)
        self._lines[index][9].setMinimum(min + 1)
        self._update_range_label(index, min, self._lines[index][9].value())
        self._update_model()

    def on_select_max_range_by_spinbox(self, max, index):
        """Callback called when the value of the maximum of the sum range spinbox is changed for a given axis.

        Args:
            max (int): the maximum value
            index (int): the index of the axis
        """
        self._lines[index][7].setHigh(max)
        self._lines[index][8].setMaximum(max - 1)
        self._update_range_label(index, self._lines[index][8].value(), max)
        self._update_model()

    def on_select_slice_by_slider(self, index):
        """Callback called when the selected slice slider value is changed for a given axis.

        Args:
            index (int): the index of the axis
        """
        value = self._lines[index][3].value()
        self._lines[index][4].blockSignals(True)
        self._lines[index][4].setValue(value)
        self._lines[index][4].blockSignals(False)
        self._update_model()

    def on_select_slice_by_spinbox(self, value, index):
        """Callback called when the selected slice spinbox value is changed for a given axis.

        Args:
            value (int): the selected slice
            index (int): the index of the axis
        """
        self._lines[index][3].blockSignals(True)
        self._lines[index][3].setValue(value)
        self._lines[index][3].blockSignals(False)

        self._update_model()

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

        self._update_range_label(index, min, max)

        self._update_model()

    def on_select_x_axis(self, states):
        """Callback called when the X axis buttongroup value is changed.

        Args:
            states (list): the states of the button group
        """
        x_axis_id = self._x_axis_button_group.checkedId()
        y_axis_id = self._y_axis_button_group.checkedId()
        if x_axis_id == y_axis_id:
            self._lines[self._current_x_index][2].setChecked(True)
            self._current_y_index = self._current_x_index
        else:
            self._lines[x_axis_id][3].setDisabled(True)
            self._lines[self._current_x_index][3].setDisabled(
                self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][4].setDisabled(True)
            self._lines[self._current_x_index][4].setDisabled(
                self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][5].setDisabled(True)
            self._lines[self._current_x_index][5].setDisabled(False)
            self._lines[x_axis_id][6].setDisabled(True)
            self._lines[self._current_x_index][6].setDisabled(
                not self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][7].setDisabled(True)
            self._lines[self._current_x_index][7].setDisabled(
                not self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][8].setDisabled(True)
            self._lines[self._current_x_index][8].setDisabled(
                not self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][9].setDisabled(True)
            self._lines[self._current_x_index][9].setDisabled(
                not self._lines[self._current_x_index][5].isChecked()
            )
            self._lines[x_axis_id][10].setDisabled(True)
            self._lines[self._current_x_index][10].setDisabled(
                not self._lines[self._current_x_index][5].isChecked()
            )

        self._current_x_index = x_axis_id

        self._update_model()

    def on_select_y_axis(self, states):
        """Callback called when the Y axis buttongroup value is changed.

        Args:
            states (list): the states of the button group
        """
        x_axis_id = self._x_axis_button_group.checkedId()
        y_axis_id = self._y_axis_button_group.checkedId()
        if x_axis_id == y_axis_id:
            self._lines[self._current_y_index][1].setChecked(True)
            self._current_x_index = self._current_y_index
        else:
            self._lines[y_axis_id][3].setDisabled(True)
            self._lines[self._current_y_index][3].setDisabled(
                self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][4].setDisabled(True)
            self._lines[self._current_y_index][4].setDisabled(
                self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][5].setDisabled(True)
            self._lines[self._current_y_index][5].setDisabled(False)
            self._lines[y_axis_id][6].setDisabled(True)
            self._lines[self._current_y_index][6].setDisabled(
                not self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][7].setDisabled(True)
            self._lines[self._current_y_index][7].setDisabled(
                not self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][8].setDisabled(True)
            self._lines[self._current_y_index][8].setDisabled(
                not self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][9].setDisabled(True)
            self._lines[self._current_y_index][9].setDisabled(
                not self._lines[self._current_y_index][5].isChecked()
            )
            self._lines[y_axis_id][10].setDisabled(True)
            self._lines[self._current_y_index][10].setDisabled(
                not self._lines[self._current_y_index][5].isChecked()
            )

        self._current_y_index = y_axis_id

        self._update_model()

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

        self._update_model()

    def on_update(self):
        """Update the widgets of the dialog."""
        x_index = self._plot_nd_model.get_x_index()
        y_index = self._plot_nd_model.get_y_index()

        self._current_x_index = x_index
        self._current_y_index = y_index

        self._lines[x_index][1].setChecked(True)
        self._lines[y_index][2].setChecked(True)

        self._lines[x_index][3].setDisabled(True)
        self._lines[y_index][3].setDisabled(True)

        self._lines[x_index][4].setDisabled(True)
        self._lines[y_index][4].setDisabled(True)

        self._lines[x_index][5].setDisabled(True)
        self._lines[y_index][5].setDisabled(True)

        self._lines[x_index][6].setDisabled(True)
        self._lines[y_index][6].setDisabled(True)

        self._lines[x_index][7].setDisabled(True)
        self._lines[y_index][7].setDisabled(True)

        self._lines[x_index][8].setDisabled(True)
        self._lines[y_index][8].setDisabled(True)

        z_data_shape = self._plot_nd_model.get_data_shape()

        axis_variables = self._plot_nd_model.get_axis_variables()
        axis_current_units = self._plot_nd_model.get_axis_current_units()
        summed_dimensions = self._plot_nd_model.get_summed_dimensions()

        for i, (variable, unit, is_summed) in enumerate(
            zip(axis_variables, axis_current_units, summed_dimensions)
        ):
            self._lines[i][0].setText(f"{variable} ({unit})")

            self._lines[i][3].setMinimum(0)
            self._lines[i][3].setMaximum(z_data_shape[i] - 1)

            self._lines[i][4].setMinimum(0)
            self._lines[i][4].setMaximum(z_data_shape[i] - 1)

            self._lines[i][5].setChecked(is_summed)

            self._lines[i][7].setMinimum(0)
            self._lines[i][7].setMaximum(z_data_shape[i] - 1)
            self._lines[i][7].setLow(0)
            self._lines[i][7].setHigh(z_data_shape[i] - 1)

            self._lines[i][8].setMinimum(0)
            self._lines[i][8].setMaximum(z_data_shape[i] - 1)
            self._lines[i][8].blockSignals(True)
            self._lines[i][8].setValue(0)
            self._lines[i][8].blockSignals(False)

            self._lines[i][9].setMinimum(0)
            self._lines[i][9].setMaximum(z_data_shape[i] - 1)
            self._lines[i][9].blockSignals(True)
            self._lines[i][9].setValue(z_data_shape[i] - 1)
            self._lines[i][9].blockSignals(False)

            self._update_range_label(i, 0, z_data_shape[i] - 1)

    def on_x_variable_updated(self):
        """Callback called when the X axis name is changed."""
        index = self._plot_nd_model.get_x_index()
        variable = self._plot_nd_model.get_x_axis_variable()
        unit = self._plot_nd_model.get_x_axis_current_unit()

        self._lines[index][0].setText(f"{variable} ({unit})")

        self._update_range_label(
            index, self._lines[index][8].value(), self._lines[index][9].value()
        )

    def on_y_variable_updated(self):
        """Callback called when the Y axis name is changed."""
        index = self._plot_nd_model.get_y_index()
        variable = self._plot_nd_model.get_y_axis_variable()
        unit = self._plot_nd_model.get_y_axis_current_unit()

        self._lines[index][0].setText(f"{variable} ({unit})")

        self._update_range_label(
            index, self._lines[index][8].value(), self._lines[index][9].value()
        )
