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

from qtpy import QtCore, QtGui, QtWidgets


<<<<<<<< HEAD:MDANSE_GUI/Src/MDANSE_GUI/Plotter/dialogs/cross_viewer_dialog.py
from MDANSE_GUI.Plotter.models.plot_1d_model import Plot1DModelError
from MDANSE_GUI.Plotter.utils.numeric import smart_round
from MDANSE_GUI.Plotter.widgets.plot_1d_widget import Plot1DWidget
from MDANSE_GUI.Plotter.widgets.range_slider import RangeSlider
========
from MDANSE_GUI.pygenplot.models.plot_1d_model import Plot1DModelError
from MDANSE_GUI.pygenplot.utils.numeric import smart_round
from MDANSE_GUI.pygenplot.widgets.plot_1d_widget import Plot1DWidget
from MDANSE_GUI.pygenplot.widgets.range_slider import RangeSlider
>>>>>>>> a3e31864e3d7a47375ecf27c20e78ea49e783dc8:MDANSE_GUI/Src/MDANSE_GUI/pygenplot/dialogs/cross_viewer_dialog.py


class CrossViewerDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, parent):
        """Constructor.

        Args:
            plot_nd_model (Plotter.models.plot_nd_model.PlotNDModel): the ND data model
            parent (qtpy.QtWidgets.QWidget): the parent widget
        """
        super(CrossViewerDialog, self).__init__(parent)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.on_update()

        self.setWindowTitle("Cross viewer dialog")

        self.resize(900, 1000)

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()

        self._x_axis_groupbox = QtWidgets.QGroupBox()

        x_axis_groupbox_layout = QtWidgets.QVBoxLayout()

        self._integrate_over_x_groupbox = QtWidgets.QGroupBox()
        self._integrate_over_x_groupbox.setTitle("Integrate over X")
        self._integrate_over_x_groupbox.setCheckable(True)
        integrate_over_x_groupbox_layout = QtWidgets.QVBoxLayout()
        range_x_layout = QtWidgets.QHBoxLayout()
        self._range_x_slider = RangeSlider(QtCore.Qt.Orientation.Horizontal)
        range_x_layout.addWidget(self._range_x_slider)
        self._min_x_spinbox = QtWidgets.QSpinBox()
        range_x_layout.addWidget(self._min_x_spinbox)
        self._max_x_spinbox = QtWidgets.QSpinBox()
        range_x_layout.addWidget(self._max_x_spinbox)
        integrate_over_x_groupbox_layout.addLayout(range_x_layout)
        self._range_x_label = QtWidgets.QLabel()
        integrate_over_x_groupbox_layout.addWidget(self._range_x_label)
        self._integrate_over_x_groupbox.setLayout(integrate_over_x_groupbox_layout)
        x_axis_groupbox_layout.addWidget(self._integrate_over_x_groupbox)
        self._x_axis_data_listview = QtWidgets.QListView()
        self._x_axis_data_listview.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        x_axis_groupbox_layout.addWidget(self._x_axis_data_listview)
        self._x_axis_groupbox.setLayout(x_axis_groupbox_layout)
        vlayout.addWidget(self._x_axis_groupbox)

        plot_x_slice_pushbutton = QtWidgets.QPushButton("Plot")
        vlayout.addWidget(plot_x_slice_pushbutton)

        hlayout.addLayout(vlayout)

        self._x_axis_slice = Plot1DWidget(
            "Line", self._plot_nd_model.get_y_axis_current_info(), self
        )
        hlayout.addWidget(self._x_axis_slice)

        main_layout.addLayout(hlayout)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        hlayout = QtWidgets.QHBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()

        self._y_axis_groupbox = QtWidgets.QGroupBox()

        y_axis_groupbox_layout = QtWidgets.QVBoxLayout()

        self._integrate_over_y_groupbox = QtWidgets.QGroupBox()
        self._integrate_over_y_groupbox.setTitle("Integrate over Y")
        self._integrate_over_y_groupbox.setCheckable(True)
        integrate_over_y_groupbox_layout = QtWidgets.QVBoxLayout()
        range_y_layout = QtWidgets.QHBoxLayout()
        self._range_y_slider = RangeSlider(QtCore.Qt.Orientation.Horizontal)
        range_y_layout.addWidget(self._range_y_slider)
        self._min_y_spinbox = QtWidgets.QSpinBox()
        range_y_layout.addWidget(self._min_y_spinbox)
        self._max_y_spinbox = QtWidgets.QSpinBox()
        range_y_layout.addWidget(self._max_y_spinbox)
        integrate_over_y_groupbox_layout.addLayout(range_y_layout)
        self._range_y_label = QtWidgets.QLabel()
        integrate_over_y_groupbox_layout.addWidget(self._range_y_label)
        self._integrate_over_y_groupbox.setLayout(integrate_over_y_groupbox_layout)
        y_axis_groupbox_layout.addWidget(self._integrate_over_y_groupbox)
        self._y_axis_data_listview = QtWidgets.QListView()
        self._y_axis_data_listview.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        y_axis_groupbox_layout.addWidget(self._y_axis_data_listview)
        self._y_axis_groupbox.setLayout(y_axis_groupbox_layout)
        vlayout.addWidget(self._y_axis_groupbox)

        plot_y_slice_pushbutton = QtWidgets.QPushButton("Plot")
        vlayout.addWidget(plot_y_slice_pushbutton)

        hlayout.addLayout(vlayout)

        self._y_axis_slice = Plot1DWidget(
            "Line", self._plot_nd_model.get_x_axis_current_info(), self
        )
        hlayout.addWidget(self._y_axis_slice)

        main_layout.addLayout(hlayout)

        self.setLayout(main_layout)

        self.finished.connect(self.on_close)

        plot_x_slice_pushbutton.clicked.connect(self.on_plot_x_slice)
        plot_y_slice_pushbutton.clicked.connect(self.on_plot_y_slice)

        self._integrate_over_x_groupbox.clicked.connect(self.on_integrate_over_x)
        self._integrate_over_y_groupbox.clicked.connect(self.on_integrate_over_y)

        self._range_x_slider.slider_moved.connect(
            lambda min, max: self.on_select_range_x_by_slider(min, max)
        )
        self._min_x_spinbox.valueChanged.connect(
            lambda value: self.on_select_min_x_range_by_spinbox(value)
        )
        self._max_x_spinbox.valueChanged.connect(
            lambda value: self.on_select_max_x_range_by_spinbox(value)
        )

        self._range_y_slider.slider_moved.connect(
            lambda min, max: self.on_select_range_y_by_slider(min, max)
        )
        self._min_y_spinbox.valueChanged.connect(
            lambda value: self.on_select_min_y_range_by_spinbox(value)
        )
        self._max_y_spinbox.valueChanged.connect(
            lambda value: self.on_select_max_y_range_by_spinbox(value)
        )

        self._plot_nd_model.x_variable_updated.connect(self.on_x_variable_updated)
        self._plot_nd_model.y_variable_updated.connect(self.on_y_variable_updated)
        self._plot_nd_model.model_updated.connect(self.on_update)

    def _update_range_x_label(self, min, max):
        """Update the label which shows the range of X values used to integrate over X axis.

        Args:
            min (float): the minimum value
            max (float): the maximum value
        """
        x_axis_current_info = self._plot_nd_model.get_x_axis_current_info()

        f = round(x_axis_current_info["data"][min], 3)
        t = round(x_axis_current_info["data"][max], 3)
        unit = x_axis_current_info["units"]
        self._range_x_label.setText(f"from {f} {unit} to {t} {unit}")

    def _update_range_y_label(self, min, max):
        """Update the label which shows the range of Y values used to integrate over Y axis.

        Args:
            min (float): the minimum value
            max (float): the maximum value
        """
        y_axis_current_info = self._plot_nd_model.get_y_axis_current_info()

        f = round(y_axis_current_info["data"][min], 3)
        t = round(y_axis_current_info["data"][max], 3)
        unit = y_axis_current_info["units"]
        self._range_y_label.setText(f"from {f} {unit} to {t} {unit}")

    def on_close(self):
        """Callback called when the dialog is closed."""
        self._plot_nd_model.unset_x_slicer()
        self._plot_nd_model.unset_y_slicer()
        self._plot_nd_model.unset_x_integration_box()
        self._plot_nd_model.unset_y_integration_box()
        self.on_update()

    def on_integrate_over_x(self, state):
        """Callback called when the integrate over X checkbox is toggled.

        Args:
            state (bool): the integrate over X checkbox state
        """
        self._x_axis_data_listview.setEnabled(not state)
        if state:
            self._plot_nd_model.unset_x_slicer()
            self._plot_nd_model.unset_y_slicer()
            min_x = self._min_x_spinbox.value()
            max_x = self._max_x_spinbox.value()
            self.on_select_x_integration_box(min_x, max_x)
        else:
            self._plot_nd_model.unset_x_integration_box()
            index = self._x_axis_data_listview.currentIndex()
            self.on_select_x_slice(index)
            index = self._y_axis_data_listview.currentIndex()
            self.on_select_y_slice(index)

    def on_integrate_over_y(self, state):
        """Callback called when the integrate over Y checkbox is toggled.

        Args:
            state (bool): the integrate over Y checkbox state
        """
        self._y_axis_data_listview.setEnabled(not state)
        if state:
            self._plot_nd_model.unset_x_slicer()
            self._plot_nd_model.unset_y_slicer()
            min_y = self._min_y_spinbox.value()
            max_y = self._max_y_spinbox.value()
            self.on_select_y_integration_box(min_y, max_y)
        else:
            self._plot_nd_model.unset_y_integration_box()
            index = self._x_axis_data_listview.currentIndex()
            self.on_select_x_slice(index)
            index = self._y_axis_data_listview.currentIndex()
            self.on_select_y_slice(index)

    def on_plot_x_slice(self):
        """Callback called when the X slice plot button is clicked."""
        integrate = self._integrate_over_x_groupbox.isChecked()
        current_x_row = self._x_axis_data_listview.currentIndex().row()
        if integrate:
            sli = slice(self._min_x_spinbox.value(), self._max_x_spinbox.value() + 1, 1)
        else:
            sli = None
            if current_x_row == -1:
                return

        x_axis_plot_1d_model = self._x_axis_slice.get_plot_1d_model()
        _, z_data_info = self._plot_nd_model.get_x_slice_info(current_x_row, sli)
        try:
            x_axis_plot_1d_model.add_line(z_data_info)
        except Plot1DModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_plot_y_slice(self):
        """Callback called when the Y slice plot button is clicked."""
        integrate = self._integrate_over_y_groupbox.isChecked()
        current_y_row = self._y_axis_data_listview.currentIndex().row()
        if integrate:
            sli = slice(self._min_y_spinbox.value(), self._max_y_spinbox.value() + 1, 1)
        else:
            sli = None
            if current_y_row == -1:
                return

        y_axis_plot_1d_model = self._y_axis_slice.get_plot_1d_model()
        _, z_data_info = self._plot_nd_model.get_y_slice_info(current_y_row, sli)
        try:
            y_axis_plot_1d_model.add_line(z_data_info)
        except Plot1DModelError as e:
            print(str(e), ["main", "popup"], "error")

    def on_select_max_x_range_by_spinbox(self, value):
        """Callback called when the maximum X value spinbox is modified.

        Args:
            value (int): the minimum value
        """
        self._range_x_slider.setHigh(value)
        self._min_x_spinbox.setMaximum(value - 1)
        self._update_range_x_label(self._min_x_spinbox.value(), value)
        min_x = self._min_x_spinbox.value()
        max_x = value
        self.on_select_x_integration_box(min_x, max_x)

    def on_select_min_x_range_by_spinbox(self, value):
        """Callback called when the minimum X value spinbox is modified.

        Args:
            value (int): the minimum value
        """
        self._range_x_slider.setLow(value)
        self._max_x_spinbox.setMinimum(value + 1)
        self._update_range_x_label(value, self._max_x_spinbox.value())
        min_x = value
        max_x = self._max_x_spinbox.value()
        self.on_select_x_integration_box(min_x, max_x)

    def on_select_max_y_range_by_spinbox(self, value):
        """Callback called when the maximum Y value spinbox is modified.

        Args:
            value (int): the minimum value
        """
        self._range_y_slider.setHigh(value)
        self._min_y_spinbox.setMaximum(value - 1)
        self._update_range_y_label(self._min_y_spinbox.value(), value)
        min_y = self._min_y_spinbox.value()
        max_y = value
        self.on_select_y_integration_box(min_y, max_y)

    def on_select_min_y_range_by_spinbox(self, value):
        """Callback called when the minimum Y value spinbox is modified.

        Args:
            value (int): the minimum value
        """
        self._range_y_slider.setLow(value)
        self._max_y_spinbox.setMinimum(value + 1)
        self._update_range_y_label(value, self._max_y_spinbox.value())
        min_y = value
        max_y = self._max_y_spinbox.value()
        self.on_select_y_integration_box(min_y, max_y)

    def on_select_range_x_by_slider(self, min, max):
        """Callback called when the X range slider is modified.

        Args:
            min (int): the minimum value
            max (int): the maximum value
        """
        self._min_x_spinbox.setMaximum(max - 1)
        self._min_x_spinbox.blockSignals(True)
        self._min_x_spinbox.setValue(min)
        self._min_x_spinbox.blockSignals(False)
        self._max_x_spinbox.setMinimum(min + 1)
        self._max_x_spinbox.blockSignals(True)
        self._max_x_spinbox.setValue(max)
        self._max_x_spinbox.blockSignals(False)

        self._update_range_x_label(min, max)

        self.on_select_x_integration_box(min, max)

    def on_select_range_y_by_slider(self, min, max):
        """Callback called when the Y range slider is modified.

        Args:
            min (int): the minimum value
            max (int): the maximum value
        """
        self._min_y_spinbox.setMaximum(max - 1)
        self._min_y_spinbox.blockSignals(True)
        self._min_y_spinbox.setValue(min)
        self._min_y_spinbox.blockSignals(False)
        self._max_y_spinbox.setMinimum(min + 1)
        self._max_y_spinbox.blockSignals(True)
        self._max_y_spinbox.setValue(max)
        self._max_y_spinbox.blockSignals(False)

        self._update_range_y_label(min, max)

        self.on_select_y_integration_box(min, max)

    def on_select_x_integration_box(self, min_x, max_x):
        """Callback called when an integration range over X is set.

        Args:
            min_x (int): the minimum x index
            max_x (int): the maximum x index
        """
        self._plot_nd_model.set_x_integration_box(min_x, max_x)

    def on_select_x_slice(self, index):
        """Callback called when a X value is selected from the X values listview.

        Args:
            index (qtpy.QtCore.QModelIndex): the selected index
        """
        current_x_row = self._x_axis_data_listview.currentIndex().row()
        if current_x_row == -1:
            return
        self._plot_nd_model.set_x_slicer(current_x_row)

    def on_select_y_integration_box(self, min_y, max_y):
        """Callback called when an integration range over Y is set.

        Args:
            min_y (int): the minimum y index
            max_y (int): the maximum y index
        """
        self._plot_nd_model.set_y_integration_box(min_y, max_y)

    def on_select_y_slice(self, index):
        """Callback called when a Y value is selected from the Y values listview.

        Args:
            index (qtpy.QtCore.QModelIndex): the selected index
        """
        current_y_row = self._y_axis_data_listview.currentIndex().row()
        if current_y_row == -1:
            return
        self._plot_nd_model.set_y_slicer(current_y_row)

    def on_update(self):
        """Update the widgets of the dialog with the current state of the ND data model."""
        x_axis_current_info = self._plot_nd_model.get_x_axis_current_info()
        y_axis_current_info = self._plot_nd_model.get_y_axis_current_info()

        self.on_x_variable_updated(x_axis_current_info["variable"])
        self.on_y_variable_updated(y_axis_current_info["variable"])

        self.on_x_data_updated(x_axis_current_info["data"])
        self.on_y_data_updated(y_axis_current_info["data"])

        x_axis_plot_1d_model = self._x_axis_slice.get_plot_1d_model()
        x_axis_plot_1d_model.reset(y_axis_current_info)
        y_axis_plot_1d_model = self._y_axis_slice.get_plot_1d_model()
        y_axis_plot_1d_model.reset(x_axis_current_info)

        self._integrate_over_x_groupbox.setChecked(False)
        self._plot_nd_model.unset_x_slicer()
        self._plot_nd_model.unset_x_integration_box()

        x_data = x_axis_current_info["data"]

        self._range_x_slider.blockSignals(True)
        self._range_x_slider.setLow(0)
        self._range_x_slider.setMinimum(0)
        self._range_x_slider.setHigh(x_data.size - 1)
        self._range_x_slider.setMaximum(x_data.size - 1)
        self._range_x_slider.blockSignals(False)

        self._min_x_spinbox.blockSignals(True)
        self._min_x_spinbox.setMinimum(0)
        self._min_x_spinbox.setMaximum(x_data.size - 1)
        self._min_x_spinbox.setValue(0)
        self._min_x_spinbox.blockSignals(False)

        self._max_x_spinbox.blockSignals(True)
        self._max_x_spinbox.setMinimum(0)
        self._max_x_spinbox.setMaximum(x_data.size - 1)
        self._max_x_spinbox.setValue(x_data.size - 1)
        self._max_x_spinbox.blockSignals(False)

        self._update_range_x_label(0, x_data.size - 1)

        self._integrate_over_y_groupbox.setChecked(False)
        self._plot_nd_model.unset_y_slicer()
        self._plot_nd_model.unset_y_integration_box()

        y_data = y_axis_current_info["data"]

        self._range_y_slider.blockSignals(True)
        self._range_y_slider.setLow(0)
        self._range_y_slider.setMinimum(0)
        self._range_y_slider.setHigh(y_data.size - 1)
        self._range_y_slider.setMaximum(y_data.size - 1)
        self._range_y_slider.blockSignals(False)

        self._min_y_spinbox.blockSignals(True)
        self._min_y_spinbox.setMinimum(0)
        self._min_y_spinbox.setMaximum(y_data.size - 1)
        self._min_y_spinbox.setValue(0)
        self._min_y_spinbox.blockSignals(False)

        self._max_y_spinbox.blockSignals(True)
        self._max_y_spinbox.setMinimum(0)
        self._max_y_spinbox.setMaximum(y_data.size - 1)
        self._max_y_spinbox.setValue(y_data.size - 1)
        self._max_y_spinbox.blockSignals(False)

        self._update_range_y_label(0, y_data.size - 1)

    def on_x_data_updated(self, x_data):
        """Callback called when the X data have changed.

        Args:
            x_data (1D-array); the X data
        """
        model = QtGui.QStandardItemModel()
        for x_value in x_data:
            v = smart_round(x_value, sigfigs=3, output="std")
            item = QtGui.QStandardItem(v)
            item.setToolTip(str(x_value))
            model.appendRow(item)
        self._x_axis_data_listview.setModel(model)
        self._x_axis_data_listview.selectionModel().currentChanged.connect(
            self.on_select_x_slice
        )

    def on_y_data_updated(self, y_data):
        """Callback called when the Y data have changed.

        Args:
            y_data (1D-array); the Y data
        """
        model = QtGui.QStandardItemModel()
        for y_value in y_data:
            v = smart_round(y_value, sigfigs=3, output="std")
            item = QtGui.QStandardItem(v)
            item.setToolTip(str(y_value))
            model.appendRow(QtGui.QStandardItem(item))
        self._y_axis_data_listview.setModel(model)
        self._y_axis_data_listview.selectionModel().currentChanged.connect(
            self.on_select_y_slice
        )

    def on_x_variable_updated(self, x_variable):
        """Callback called when the name of the X axis has changed.

        Args:
            x_variable (str): the X axis name
        """
        self._x_axis_groupbox.setTitle(f"X Axis ({x_variable})")

    def on_y_variable_updated(self, y_variable):
        """Callback called when the name of the Y axis has changed.

        Args:
            y_variable (str): the Y axis name
        """
        self._y_axis_groupbox.setTitle(f"Y Axis ({y_variable})")
