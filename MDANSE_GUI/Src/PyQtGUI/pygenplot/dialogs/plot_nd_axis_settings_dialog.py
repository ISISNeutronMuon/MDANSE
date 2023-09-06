import numpy as np

from qtpy import QtWidgets


from MDANSE_GUI.PyQtGUI.pygenplot.models.plot_nd_model import (
    PlotNDModel,
    PlotNDModelError,
)


class PlotNDAxisSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, parent):
        """Constructor.

        Args:
            plot_nd_model (pygenplot.models.plot_nd_model.PlotNDmodel): the ND data model
            parent (qtpy.QtCore.QObject): the parent
        """
        super(PlotNDAxisSettingsDialog, self).__init__(parent)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.on_update()

        self.setWindowTitle("Axis settings dialog")

        self.resize(500, 200)

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()

        x_axis_groupbox = QtWidgets.QGroupBox("X axis")
        x_axis_layout = QtWidgets.QFormLayout()
        x_label_label = QtWidgets.QLabel("Label")
        self._x_label_lineedit = QtWidgets.QLineEdit()
        x_axis_layout.addRow(x_label_label, self._x_label_lineedit)
        x_units_label = QtWidgets.QLabel("Units")
        hlayout = QtWidgets.QHBoxLayout()
        self._x_units_lineedit = QtWidgets.QLineEdit()
        x_units_push_button = QtWidgets.QPushButton("Set")
        hlayout.addWidget(self._x_units_lineedit)
        hlayout.addWidget(x_units_push_button)
        x_axis_layout.addRow(x_units_label, hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self._new_min_x_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._new_min_x_doublespinbox.setMinimum(-np.inf)
        self._new_min_x_doublespinbox.setMaximum(np.inf)
        self._new_min_x_doublespinbox.setSingleStep(1.0e-03)
        self._new_min_x_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._new_max_x_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._new_max_x_doublespinbox.setMinimum(-np.inf)
        self._new_max_x_doublespinbox.setMaximum(np.inf)
        self._new_max_x_doublespinbox.setSingleStep(1.0e-03)
        self._new_max_x_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._new_x_units_lineedit = QtWidgets.QLineEdit()
        new_x_units_push_button = QtWidgets.QPushButton("Reset")
        hlayout.addWidget(QtWidgets.QLabel("Min"))
        hlayout.addWidget(self._new_min_x_doublespinbox, 1)
        hlayout.addWidget(QtWidgets.QLabel("Max"))
        hlayout.addWidget(self._new_max_x_doublespinbox, 1)
        hlayout.addWidget(QtWidgets.QLabel("New unit"))
        hlayout.addWidget(self._new_x_units_lineedit, 1)
        hlayout.addWidget(new_x_units_push_button)
        x_axis_layout.addRow(QtWidgets.QLabel(""), hlayout)
        x_axis_groupbox.setLayout(x_axis_layout)
        vlayout.addWidget(x_axis_groupbox)

        y_axis_groupbox = QtWidgets.QGroupBox("Y axis")
        y_axis_layout = QtWidgets.QFormLayout()
        y_label_label = QtWidgets.QLabel("Label")
        self._y_label_lineedit = QtWidgets.QLineEdit()
        y_axis_layout.addRow(y_label_label, self._y_label_lineedit)
        y_units_label = QtWidgets.QLabel("Units")
        hlayout = QtWidgets.QHBoxLayout()
        self._y_units_lineedit = QtWidgets.QLineEdit()
        y_units_push_button = QtWidgets.QPushButton("Set")
        hlayout.addWidget(self._y_units_lineedit)
        hlayout.addWidget(y_units_push_button)
        y_axis_layout.addRow(y_units_label, hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self._new_min_y_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._new_min_y_doublespinbox.setMinimum(-np.inf)
        self._new_min_y_doublespinbox.setMaximum(np.inf)
        self._new_min_y_doublespinbox.setSingleStep(1.0e-03)
        self._new_min_y_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._new_max_y_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._new_max_y_doublespinbox.setMinimum(-np.inf)
        self._new_max_y_doublespinbox.setMaximum(np.inf)
        self._new_max_y_doublespinbox.setSingleStep(1.0e-03)
        self._new_max_y_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._new_y_units_lineedit = QtWidgets.QLineEdit()
        new_y_units_push_button = QtWidgets.QPushButton("Reset")
        hlayout.addWidget(QtWidgets.QLabel("Min"))
        hlayout.addWidget(self._new_min_y_doublespinbox, 1)
        hlayout.addWidget(QtWidgets.QLabel("Max"))
        hlayout.addWidget(self._new_max_y_doublespinbox, 1)
        hlayout.addWidget(QtWidgets.QLabel("New unit"))
        hlayout.addWidget(self._new_y_units_lineedit, 1)
        hlayout.addWidget(new_y_units_push_button)
        y_axis_layout.addRow(QtWidgets.QLabel(""), hlayout)
        y_axis_groupbox.setLayout(y_axis_layout)
        vlayout.addWidget(y_axis_groupbox)

        z_axis_groupbox = QtWidgets.QGroupBox("Z axis")
        z_axis_layout = QtWidgets.QFormLayout()
        z_label_label = QtWidgets.QLabel("Label")
        self._z_label_lineedit = QtWidgets.QLineEdit()
        z_range_label = QtWidgets.QLabel("Range")
        hlayout = QtWidgets.QHBoxLayout()
        min_label = QtWidgets.QLabel("Min")
        hlayout.addWidget(min_label)
        self._min_z_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._min_z_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._min_z_doublespinbox.setMinimum(-np.inf)
        self._min_z_doublespinbox.setMaximum(np.inf)
        self._min_z_doublespinbox.setDecimals(3)
        self._min_z_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._min_z_doublespinbox, 1)
        max_label = QtWidgets.QLabel("Max")
        hlayout.addWidget(max_label)
        self._max_z_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._max_z_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._max_z_doublespinbox.setMinimum(-np.inf)
        self._max_z_doublespinbox.setMaximum(np.inf)
        self._max_z_doublespinbox.setDecimals(3)
        self._max_z_doublespinbox.setSingleStep(1.0e-03)
        hlayout.addWidget(self._max_z_doublespinbox, 1)
        set_z_range_pushbutton = QtWidgets.QPushButton("Set")
        hlayout.addWidget(set_z_range_pushbutton)
        default_z_range_pushbutton = QtWidgets.QPushButton("Default")
        hlayout.addWidget(default_z_range_pushbutton)
        z_axis_layout.addRow(z_range_label, hlayout)
        z_axis_layout.addRow(z_label_label, self._z_label_lineedit)
        z_units_label = QtWidgets.QLabel("Units")
        hlayout = QtWidgets.QHBoxLayout()
        self._z_units_lineedit = QtWidgets.QLineEdit()
        z_units_push_button = QtWidgets.QPushButton("Set")
        hlayout.addWidget(self._z_units_lineedit)
        hlayout.addWidget(z_units_push_button)
        z_axis_layout.addRow(z_units_label, hlayout)
        z_scale_label = QtWidgets.QLabel("Scale")
        self._z_scale_combobox = QtWidgets.QComboBox()
        z_axis_layout.addRow(z_scale_label, self._z_scale_combobox)
        z_axis_groupbox.setLayout(z_axis_layout)
        vlayout.addWidget(z_axis_groupbox)

        main_layout.addLayout(vlayout)

        self.setLayout(main_layout)

        self._x_label_lineedit.textEdited.connect(self.on_edit_x_label)
        self._y_label_lineedit.textEdited.connect(self.on_edit_y_label)
        self._z_label_lineedit.textEdited.connect(self.on_edit_z_label)

        x_units_push_button.clicked.connect(self.on_change_x_unit)
        y_units_push_button.clicked.connect(self.on_change_y_unit)
        z_units_push_button.clicked.connect(self.on_change_z_unit)
        new_x_units_push_button.clicked.connect(self.on_reset_x_unit)
        new_y_units_push_button.clicked.connect(self.on_reset_y_unit)

        set_z_range_pushbutton.clicked.connect(self.on_set_z_range)
        default_z_range_pushbutton.clicked.connect(self.on_set_default_z_range)
        self._z_scale_combobox.activated.connect(self.on_change_z_scale)

        self._plot_nd_model.model_updated.connect(self.on_update_axis)

    def on_change_x_unit(self):
        """Callback called when the X axis unit is changed."""
        new_x_unit = self._x_units_lineedit.text()
        try:
            self._plot_nd_model.set_x_axis_unit(new_x_unit)
        except PlotNDModelError:
            print("Incompatible X unit", ["main", "popup"], "error")
            return

    def on_change_y_unit(self):
        """Callback called when the Y axis unit is changed."""
        new_y_unit = self._y_units_lineedit.text()
        try:
            self._plot_nd_model.set_y_axis_unit(new_y_unit)
        except PlotNDModelError:
            print("Incompatible Y unit", ["main", "popup"], "error")
            return

    def on_change_z_scale(self, index):
        """Callback called when the Z axis scale combobox value is changed.

        Args:
            index (int): the index of the selected Z axis scale item
        """
        self._plot_nd_model.set_norm(self._z_scale_combobox.currentText())

    def on_change_z_unit(self):
        """Callback called when the Z axis unit is changed."""
        new_z_unit = self._z_units_lineedit.text()
        try:
            self._plot_nd_model.set_data_current_unit(new_z_unit)
        except PlotNDModelError:
            print("Incompatible Z unit", ["main", "popup"], "error")
            return

    def on_edit_x_label(self, label):
        """Callback called when the X axis label is edited.

        Args:
            label (str): the X axis label
        """
        self._plot_nd_model.set_x_axis_label(label)

    def on_edit_y_label(self, label):
        """Callback called when the Y axis label is edited.

        Args:
            label (str): the Y axis label
        """
        self._plot_nd_model.set_y_axis_label(label)

    def on_edit_z_label(self, label):
        """Callback called when the Z axis label is edited.

        Args:
            label (str): the Z axis label
        """
        self._plot_nd_model.set_data_label(label)

    def on_reset_x_unit(self):
        """Callback called when the reset X axis button is cliked."""
        min_x = self._new_min_x_doublespinbox.value()
        max_x = self._new_max_x_doublespinbox.value()
        if max_x <= min_x:
            print("Invalid min/max values", ["main", "popup"], "error")
            return

        new_unit = self._new_x_units_lineedit.text().strip()
        if not new_unit:
            print("No unit defined", ["main", "popup"], "error")
            return

        try:
            self._plot_nd_model.reset_x_axis(min_x, max_x, new_unit)
        except PlotNDModelError as e:
            print(str(e), ["main", "popup"], "error")
            return
        else:
            self._x_units_lineedit.setText(new_unit)

    def on_reset_y_unit(self):
        """Callback called when the reset Y axis button is cliked."""
        min_y = self._new_min_y_doublespinbox.value()
        max_y = self._new_max_y_doublespinbox.value()

        new_unit = self._new_y_units_lineedit.text()

        try:
            self._plot_nd_model.reset_y_axis(min_y, max_y, new_unit)
        except PlotNDModelError as e:
            print(str(e), ["main", "popup"], "error")
            return
        else:
            self._x_units_lineedit.setText(new_unit)

    def on_set_default_z_range(self):
        """Callback called when the Z range default button is clicked."""
        min_z, max_z = self._plot_nd_model.get_data_range()
        self._min_z_doublespinbox.setValue(min_z)
        self._max_z_doublespinbox.setValue(max_z)
        self.on_set_z_range()

    def on_set_z_range(self):
        """Callback when the set Z range button is clicked."""
        min_z = self._min_z_doublespinbox.value()
        max_z = self._max_z_doublespinbox.value()
        try:
            self._plot_nd_model.set_data_range(min_z, max_z)
        except PlotNDModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_update(self):
        """Update the widgets of the dialog."""
        self.on_update_axis()

        self._z_label_lineedit.setText(self._plot_nd_model.get_data_variable())
        min_z, max_z = self._plot_nd_model.get_data_range()
        self._min_z_doublespinbox.setValue(min_z)
        self._max_z_doublespinbox.setValue(max_z)

        self._z_units_lineedit.setText(self._plot_nd_model.get_data_current_unit())

        self._z_scale_combobox.clear()
        self._z_scale_combobox.addItems(PlotNDModel.normalizers)
        self._z_scale_combobox.setCurrentText(self._plot_nd_model.get_norm())

    def on_update_axis(self):
        """Update the X and Y axis lineedit widgets."""
        self._x_label_lineedit.setText(self._plot_nd_model.get_x_axis_variable())
        self._y_label_lineedit.setText(self._plot_nd_model.get_y_axis_variable())
        self._x_units_lineedit.setText(self._plot_nd_model.get_x_axis_current_unit())
        self._y_units_lineedit.setText(self._plot_nd_model.get_y_axis_current_unit())
