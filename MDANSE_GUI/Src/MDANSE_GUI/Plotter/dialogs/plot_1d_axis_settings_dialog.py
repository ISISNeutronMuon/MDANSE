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

from qtpy import QtWidgets


from MDANSE_GUI.Plotter.models.plot_1d_model import (
    Plot1DModel,
    Plot1DModelError,
)


class Plot1DAxisSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_1d_model, parent):
        """Constructor.

        Args:
            plot_1d_model (Plotter.models.plot_1d_model.Plot1DModel): the 1D data model
            parent (qtpy.QtCore.QObject): the parent
        """
        super(Plot1DAxisSettingsDialog, self).__init__(parent)

        self._plot_1d_model = plot_1d_model

        self._build()

        self.on_update()

        self.setWindowTitle("Axis settings dialog")

        self.resize(400, -1)

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()
        axis_layout = QtWidgets.QVBoxLayout()

        x_axis_groupbox = QtWidgets.QGroupBox("X axis")
        x_axis_groupbox_layout = QtWidgets.QFormLayout()
        x_label_label = QtWidgets.QLabel("Label")
        self._x_label_lineedit = QtWidgets.QLineEdit()
        x_axis_groupbox_layout.addRow(x_label_label, self._x_label_lineedit)
        x_range_label = QtWidgets.QLabel("Range")
        hlayout = QtWidgets.QHBoxLayout()
        x_min_label = QtWidgets.QLabel("Min")
        hlayout.addWidget(x_min_label)
        self._x_min_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._x_min_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._x_min_doublespinbox.setMinimum(-np.inf)
        self._x_min_doublespinbox.setMaximum(np.inf)
        self._x_min_doublespinbox.setDecimals(3)
        self._x_min_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._x_min_doublespinbox, 1)
        x_max_label = QtWidgets.QLabel("Max")
        hlayout.addWidget(x_max_label)
        self._x_max_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._x_max_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._x_max_doublespinbox.setMinimum(-np.inf)
        self._x_max_doublespinbox.setMaximum(np.inf)
        self._x_max_doublespinbox.setDecimals(3)
        self._x_max_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._x_max_doublespinbox, 1)
        set_x_range_pushbutton = QtWidgets.QPushButton("Set")
        hlayout.addWidget(set_x_range_pushbutton)
        x_axis_groupbox_layout.addRow(x_range_label, hlayout)
        x_units_label = QtWidgets.QLabel("Units")
        units_hlayout = QtWidgets.QHBoxLayout()
        self._x_units_lineedit = QtWidgets.QLineEdit()
        x_units_pushbutton = QtWidgets.QPushButton("Set")
        units_hlayout.addWidget(self._x_units_lineedit)
        units_hlayout.addWidget(x_units_pushbutton)
        x_axis_groupbox_layout.addRow(x_units_label, units_hlayout)
        x_scale_label = QtWidgets.QLabel("Scale")
        self._x_scale_combobox = QtWidgets.QComboBox()
        x_axis_groupbox_layout.addRow(x_scale_label, self._x_scale_combobox)
        x_axis_groupbox.setLayout(x_axis_groupbox_layout)
        axis_layout.addWidget(x_axis_groupbox)

        y_axis_groupbox = QtWidgets.QGroupBox("Y axis")
        y_axis_groupbox_layout = QtWidgets.QFormLayout()
        y_label_label = QtWidgets.QLabel("Label")
        self._y_label_lineedit = QtWidgets.QLineEdit()
        y_axis_groupbox_layout.addRow(y_label_label, self._y_label_lineedit)
        y_range_label = QtWidgets.QLabel("Range")
        hlayout = QtWidgets.QHBoxLayout()
        y_min_label = QtWidgets.QLabel("Min")
        hlayout.addWidget(y_min_label)
        self._y_min_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._y_min_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._y_min_doublespinbox.setMinimum(-np.inf)
        self._y_min_doublespinbox.setMaximum(np.inf)
        self._y_min_doublespinbox.setDecimals(3)
        self._y_min_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._y_min_doublespinbox, 1)
        y_max_label = QtWidgets.QLabel("Max")
        hlayout.addWidget(y_max_label)
        self._y_max_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._y_max_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._y_max_doublespinbox.setMinimum(-np.inf)
        self._y_max_doublespinbox.setMaximum(np.inf)
        self._y_max_doublespinbox.setDecimals(3)
        self._y_max_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._y_max_doublespinbox, 1)
        set_y_range_pushbutton = QtWidgets.QPushButton("Set")
        hlayout.addWidget(set_y_range_pushbutton)
        y_axis_groupbox_layout.addRow(y_range_label, hlayout)
        y_units_label = QtWidgets.QLabel("Units")
        units_hlayout = QtWidgets.QHBoxLayout()
        self._y_units_lineedit = QtWidgets.QLineEdit()
        y_units_pushbutton = QtWidgets.QPushButton("Set")
        units_hlayout.addWidget(self._y_units_lineedit)
        units_hlayout.addWidget(y_units_pushbutton)
        y_axis_groupbox_layout.addRow(y_units_label, units_hlayout)
        y_scale_label = QtWidgets.QLabel("Scale")
        self._y_scale_combobox = QtWidgets.QComboBox()
        y_axis_groupbox_layout.addRow(y_scale_label, self._y_scale_combobox)
        y_axis_groupbox.setLayout(y_axis_groupbox_layout)
        axis_layout.addWidget(y_axis_groupbox)

        adjust_axes_pushbutton = QtWidgets.QPushButton("adjust axes")

        vlayout.addLayout(axis_layout)
        vlayout.addWidget(adjust_axes_pushbutton)

        main_layout.addLayout(vlayout)

        self.setLayout(main_layout)

        set_x_range_pushbutton.clicked.connect(self.on_set_x_range)
        set_y_range_pushbutton.clicked.connect(self.on_set_y_range)

        self._x_label_lineedit.textEdited.connect(self.on_edit_x_label)
        self._y_label_lineedit.textEdited.connect(self.on_edit_y_label)

        self._x_scale_combobox.activated.connect(self.on_change_x_scale)
        self._y_scale_combobox.activated.connect(self.on_change_y_scale)

        x_units_pushbutton.clicked.connect(self.on_change_x_unit)
        y_units_pushbutton.clicked.connect(self.on_change_y_unit)

        adjust_axes_pushbutton.clicked.connect(self.on_adjust_axes)

    def on_adjust_axes(self):
        """Callback called when the button for adjusting axes is clicked."""
        limits = self._plot_1d_model.adjust_axes()
        self._x_min_doublespinbox.setValue(limits[0])
        self._x_max_doublespinbox.setValue(limits[1])
        self._y_min_doublespinbox.setValue(limits[2])
        self._y_max_doublespinbox.setValue(limits[3])

    def on_change_x_scale(self, index):
        """Callback called when the the X axis combobox is modified.

        Args:
            index (int): the index of the selected scale
        """
        self._plot_1d_model.set_x_axis_scale(self._x_scale_combobox.currentText())

    def on_change_x_unit(self):
        """Callback called when the X axis unit is changed."""
        new_x_unit = self._x_units_lineedit.text()
        try:
            self._plot_1d_model.set_x_axis_unit(new_x_unit)
        except Plot1DModelError:
            print("Incompatible X unit", ["main", "popup"], "error")
            return

    def on_change_y_scale(self, index):
        """Callback called when the the Y axis combobox is modified.

        Args:
            index (int): the index of the selected scale
        """
        self._plot_1d_model.set_y_axis_scale(self._y_scale_combobox.currentText())

    def on_change_y_unit(self):
        """Callback called when the X axis unit is changed."""
        new_y_unit = self._y_units_lineedit.text()
        try:
            self._plot_1d_model.set_y_axis_unit(new_y_unit)
        except Plot1DModelError:
            print("Incompatible Y unit", ["main", "popup"], "error")
            return

    def on_edit_x_label(self, label):
        """Callback called when the X axis label is edited.

        Args:
            label (str): the new label
        """
        self._plot_1d_model.set_x_axis_label(label)

    def on_edit_y_label(self, label):
        """Callback called when the Y axis label is edited.

        Args:
            label (str): the new label
        """
        self._plot_1d_model.set_y_axis_label(label)

    def on_set_x_range(self):
        """Callback called when the X axis range is modified."""
        x_min = self._x_min_doublespinbox.value()
        x_max = self._x_max_doublespinbox.value()
        try:
            self._plot_1d_model.set_x_axis_range(x_min, x_max)
        except Plot1DModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_set_y_range(self):
        """Callback called when the Y axis range is modified."""
        y_min = self._y_min_doublespinbox.value()
        y_max = self._y_max_doublespinbox.value()
        try:
            self._plot_1d_model.set_y_axis_range(y_min, y_max)
        except Plot1DModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_update(self):
        """Update the widgets of the dialog."""
        self._x_label_lineedit.setText(self._plot_1d_model.get_x_axis_variable())

        self._x_min_doublespinbox.setValue(self._plot_1d_model.get_x_axis_min_value())

        self._x_max_doublespinbox.setValue(self._plot_1d_model.get_x_axis_max_value())

        self._x_units_lineedit.setText(self._plot_1d_model.get_x_axis_current_unit())

        self._x_scale_combobox.clear()
        self._x_scale_combobox.addItems(Plot1DModel.scales)
        self._x_scale_combobox.setCurrentText(self._plot_1d_model.get_x_axis_scale())

        self._y_label_lineedit.setText(self._plot_1d_model.get_y_axis_label())

        self._y_min_doublespinbox.setValue(self._plot_1d_model.get_y_axis_min_value())

        self._y_max_doublespinbox.setValue(self._plot_1d_model.get_y_axis_max_value())

        self._y_units_lineedit.setText(self._plot_1d_model.get_y_axis_current_unit())

        self._y_scale_combobox.clear()
        self._y_scale_combobox.addItems(Plot1DModel.scales)
        self._y_scale_combobox.setCurrentText(self._plot_1d_model.get_y_axis_scale())
