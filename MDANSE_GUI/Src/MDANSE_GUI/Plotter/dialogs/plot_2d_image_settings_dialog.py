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

from qtpy import QtWidgets


from MDANSE_GUI.Plotter.models.plot_2d_model import (
    Plot2DModel,
    Plot2DModelError,
)


class Plot2DImageSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_2d_model, parent):
        super(Plot2DImageSettingsDialog, self).__init__(parent)

        self._plot_2d_model = plot_2d_model

        self._build()

        self.setWindowTitle("Image settings dialog")

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()

        x_axis_groupbox = QtWidgets.QGroupBox("X axis")
        x_axis_layout = QtWidgets.QFormLayout()
        x_label_label = QtWidgets.QLabel("Label")
        x_label_lineedit = QtWidgets.QLineEdit(self._plot_2d_model.get_x_variable())
        x_axis_layout.addRow(x_label_label, x_label_lineedit)
        x_units_label = QtWidgets.QLabel("Units")
        self._x_units_lineedit = QtWidgets.QLineEdit()
        self._x_units_lineedit.setText(self._plot_2d_model.get_x_current_unit())
        x_axis_layout.addRow(x_units_label, self._x_units_lineedit)
        x_axis_groupbox.setLayout(x_axis_layout)
        vlayout.addWidget(x_axis_groupbox)

        y_axis_groupbox = QtWidgets.QGroupBox("Y axis")
        y_axis_layout = QtWidgets.QFormLayout()
        y_label_label = QtWidgets.QLabel("Label")
        y_label_lineedit = QtWidgets.QLineEdit(self._plot_2d_model.get_y_variable())
        y_axis_layout.addRow(y_label_label, y_label_lineedit)
        y_units_label = QtWidgets.QLabel("Units")
        self._y_units_lineedit = QtWidgets.QLineEdit()
        self._y_units_lineedit.setText(self._plot_2d_model.get_y_current_unit())
        y_axis_layout.addRow(y_units_label, self._y_units_lineedit)
        y_axis_groupbox.setLayout(y_axis_layout)
        vlayout.addWidget(y_axis_groupbox)

        z_axis_groupbox = QtWidgets.QGroupBox("Z axis")
        z_axis_layout = QtWidgets.QFormLayout()
        z_label_label = QtWidgets.QLabel("Label")
        z_label_lineedit = QtWidgets.QLineEdit(self._plot_2d_model.get_z_variable())
        z_axis_layout.addRow(z_label_label, z_label_lineedit)
        z_units_label = QtWidgets.QLabel("Units")
        self._z_units_lineedit = QtWidgets.QLineEdit()
        self._z_units_lineedit.setText(self._plot_2d_model.get_z_current_unit())
        z_axis_layout.addRow(z_units_label, self._z_units_lineedit)
        z_axis_groupbox.setLayout(z_axis_layout)
        vlayout.addWidget(z_axis_groupbox)

        image_groupbox = QtWidgets.QGroupBox("Image")
        image_layout = QtWidgets.QFormLayout()
        aspect_label = QtWidgets.QLabel("Aspect")
        aspect_combobox = QtWidgets.QComboBox()
        aspect_combobox.addItems(Plot2DModel.aspects)
        aspect_combobox.setCurrentText(self._plot_2d_model.get_aspect())
        image_layout.addRow(aspect_label, aspect_combobox)
        interpolation_label = QtWidgets.QLabel("Interpolation")
        interpolation_combobox = QtWidgets.QComboBox()
        interpolation_combobox.addItems(Plot2DModel.interpolations)
        interpolation_combobox.setCurrentText(self._plot_2d_model.get_interpolation())
        image_layout.addRow(interpolation_label, interpolation_combobox)
        cmap_label = QtWidgets.QLabel("Color map")
        cmap_combobox = QtWidgets.QComboBox()
        cmap_combobox.addItems(Plot2DModel.cmaps)
        cmap_combobox.setCurrentText(self._plot_2d_model.get_cmap())
        image_layout.addRow(cmap_label, cmap_combobox)
        add_colorbar_label = QtWidgets.QLabel("Add colorbar")
        add_colorbar_checkbox = QtWidgets.QCheckBox("")
        add_colorbar_checkbox.setChecked(self._plot_2d_model.add_colorbar())
        image_layout.addRow(add_colorbar_label, add_colorbar_checkbox)
        image_groupbox.setLayout(image_layout)
        vlayout.addWidget(image_groupbox)

        main_layout.addLayout(vlayout)

        buttons_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        main_layout.addWidget(buttons_box)

        self.setLayout(main_layout)

        buttons_box.rejected.connect(self.reject)
        buttons_box.accepted.connect(self.accept)

        x_label_lineedit.textEdited.connect(self.on_edit_x_label)
        y_label_lineedit.textEdited.connect(self.on_edit_y_label)
        z_label_lineedit.textEdited.connect(self.on_edit_z_label)

        self._x_units_lineedit.editingFinished.connect(self.on_change_x_unit)
        self._y_units_lineedit.editingFinished.connect(self.on_change_y_unit)
        self._z_units_lineedit.editingFinished.connect(self.on_change_z_unit)

        aspect_combobox.currentTextChanged.connect(self.on_change_aspect)
        interpolation_combobox.currentTextChanged.connect(self.on_change_interpolation)
        cmap_combobox.currentTextChanged.connect(self.on_change_cmap)

        add_colorbar_checkbox.stateChanged.connect(self.on_add_colorbar)

    def on_add_colorbar(self, state):
        self._plot_2d_model.toggle_colorbar(state)

    def on_change_aspect(self, aspect):
        self._plot_2d_model.set_aspect(aspect)

    def on_change_cmap(self, cmap):
        self._plot_2d_model.set_cmap(cmap)

    def on_change_interpolation(self, interpolation):
        self._plot_2d_model.set_interpolation(interpolation)

    def on_change_x_unit(self):
        new_x_unit = self._x_units_lineedit.text()
        try:
            self._plot_2d_model.set_x_unit(new_x_unit)
        except Plot2DModelError:
            print("Incompatible X unit", ["main", "popup"], "error")
            return

    def on_change_y_unit(self):
        new_y_unit = self._y_units_lineedit.text()
        try:
            self._plot_2d_model.set_y_unit(new_y_unit)
        except Plot2DModelError:
            print("Incompatible Y unit", ["main", "popup"], "error")
            return

    def on_change_z_unit(self):
        new_z_unit = self._z_units_lineedit.text()
        try:
            self._plot_2d_model.set_z_unit(new_z_unit)
        except Plot2DModelError:
            print("Incompatible Z unit", ["main", "popup"], "error")
            return

    def on_edit_x_label(self, label):
        self._plot_2d_model.set_x_axis_label(label)

    def on_edit_y_label(self, label):
        self._plot_2d_model.set_y_axis_label(label)

    def on_edit_z_label(self, label):
        self._plot_2d_model.set_z_axis_label(label)
