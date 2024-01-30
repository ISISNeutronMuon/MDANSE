# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     root file of pygenplot
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

import numpy as np

from qtpy import QtCore, QtWidgets

from MDANSE_GUI.pygenplot.models.plot_1d_model import Plot1DModel


class Plot1DLinesSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_1d_model, parent):
        """Constructor.

        Args:
            plot_1d_model (pygenplot.models.plot_1d_model.Plot1DModel): the 1D data model
            parent (qtpy.QtCore.QObject): the parent
        """
        super(Plot1DLinesSettingsDialog, self).__init__(parent)

        self._plot_1d_model = plot_1d_model

        self._build()

        self.on_update()

        self.setWindowTitle("Lines settings dialog")

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        self._lines_listview = QtWidgets.QListView()
        self._lines_listview.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self._lines_listview.setModel(self._plot_1d_model)
        self._lines_listview.installEventFilter(self)

        line_settings_groupbox = QtWidgets.QGroupBox(self)
        line_settings_groupbox.setTitle("Settings")
        line_settings_groupbox_layout = QtWidgets.QFormLayout()
        line_style_label = QtWidgets.QLabel("Style")
        self._line_style_combobox = QtWidgets.QComboBox()
        line_settings_groupbox_layout.addRow(
            line_style_label, self._line_style_combobox
        )
        marker_style_label = QtWidgets.QLabel("Marker")
        self._marker_style_combobox = QtWidgets.QComboBox()
        line_settings_groupbox_layout.addRow(
            marker_style_label, self._marker_style_combobox
        )
        line_width_label = QtWidgets.QLabel("Width")
        self._line_width_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._line_width_doublespinbox.setMinimum(0)
        self._line_width_doublespinbox.setMaximum(10)
        self._line_width_doublespinbox.setSingleStep(0.1)
        self._line_width_doublespinbox.setDecimals(1)
        line_settings_groupbox_layout.addRow(
            line_width_label, self._line_width_doublespinbox
        )
        line_color_label = QtWidgets.QLabel("Color")
        self._line_color_pushbutton = QtWidgets.QPushButton()
        line_settings_groupbox_layout.addRow(
            line_color_label, self._line_color_pushbutton
        )
        line_settings_groupbox.setLayout(line_settings_groupbox_layout)
        hlayout.addWidget(self._lines_listview)
        hlayout.addWidget(line_settings_groupbox)
        main_layout.addLayout(hlayout)

        line_splitter_groupbox = QtWidgets.QGroupBox()
        line_splitter_groupbox.setTitle("Line splitter")
        line_splitter_groupbox_layout = QtWidgets.QFormLayout()
        line_splitter_maximum_offset_label = QtWidgets.QLabel("Offset")
        self._line_splitter_maximum_offset_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._line_splitter_maximum_offset_doublespinbox.setMinimum(-np.inf)
        self._line_splitter_maximum_offset_doublespinbox.setMaximum(np.inf)
        line_splitter_groupbox_layout.addRow(
            line_splitter_maximum_offset_label,
            self._line_splitter_maximum_offset_doublespinbox,
        )
        line_splitter_factor_label = QtWidgets.QLabel("Factor")
        hlayout = QtWidgets.QHBoxLayout()
        self._line_splitter_factor_slider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal
        )
        self._line_splitter_factor_slider.setMinimum(0)
        self._line_splitter_factor_slider.setMaximum(100)
        self._line_splitter_factor_slider.setSingleStep(1)
        self._line_splitter_factor_slider.setValue(
            int(100 * self._plot_1d_model.get_line_splitter_factor())
        )
        self._line_splitter_factor_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._line_splitter_factor_doublespinbox.setMinimum(0.0)
        self._line_splitter_factor_doublespinbox.setMaximum(1.0)
        self._line_splitter_factor_doublespinbox.setSingleStep(1.0e-02)
        self._line_splitter_factor_doublespinbox.setValue(
            self._plot_1d_model.get_line_splitter_factor()
        )
        hlayout.addWidget(self._line_splitter_factor_slider)
        hlayout.addWidget(self._line_splitter_factor_doublespinbox)
        line_splitter_groupbox_layout.addRow(line_splitter_factor_label, hlayout)
        line_splitter_groupbox.setLayout(line_splitter_groupbox_layout)
        main_layout.addWidget(line_splitter_groupbox)

        self.setLayout(main_layout)

        self.finished.connect(self.on_close)

        self._lines_listview.selectionModel().currentRowChanged.connect(
            self.on_select_line
        )
        self._line_style_combobox.activated.connect(self.on_change_line_style)
        self._marker_style_combobox.activated.connect(self.on_change_marker_style)
        self._line_width_doublespinbox.valueChanged.connect(self.on_change_line_width)
        self._line_color_pushbutton.clicked.connect(self.on_change_line_color)

        self._line_splitter_maximum_offset_doublespinbox.valueChanged.connect(
            self.on_change_line_splitter_maximum_offset
        )
        self._line_splitter_factor_slider.valueChanged.connect(
            self.on_change_line_splitter_factor_slider_value
        )
        self._line_splitter_factor_doublespinbox.valueChanged.connect(
            self.on_change_line_splitter_factor_doublespinbox_value
        )

    def eventFilter(self, source, event):
        """Event filter for the dialog.

        Args:
            source (qtpy.QtWidgets.QWidget): the widget triggering the event
            event (qtpy.QtCore.QEvent): the event
        """
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Delete:
                if source == self._lines_listview:
                    self._plot_1d_model.removeRow(
                        self._lines_listview.currentIndex().row(), QtCore.QModelIndex()
                    )

        return super(Plot1DLinesSettingsDialog, self).eventFilter(source, event)

    def _change_line_splitter_factor(self, value):
        """Change the line splitter factor.

        Args:
            value (float): the line splitter factor
        """
        self._plot_1d_model.set_line_splitter_factor(value)

    def on_change_line_splitter_factor_doublespinbox_value(self, value):
        """Callback called when the line splitter factor double spinbox value is changed.

        Args:
            value (float): the line splitter factor value
        """
        slider_value = int(value * self._line_splitter_factor_slider.maximum())
        self._line_splitter_factor_slider.setValue(slider_value)
        self._change_line_splitter_factor(value)

    def on_change_line_splitter_factor_slider_value(self, value):
        """Callback called when the line splitter factor slider value is changed.

        Args:
            value (int): the line splitter factor value
        """
        factor = value / self._line_splitter_factor_slider.maximum()
        self._line_splitter_factor_doublespinbox.setValue(factor)
        self._change_line_splitter_factor(factor)

    def on_change_line_splitter_maximum_offset(self, value):
        """Callback called when the line splitter maximum offset double spinbox value is changed.

        Args:
            value (float): the line splitter maximum offset value
        """
        self._plot_1d_model.set_line_splitter_maximum_offset(value)

    def on_change_line_style(self, index):
        """Callback called when the line style comboxbox value is changed.

        Args:
            index (int): the index of the selected line style item
        """
        self._plot_1d_model.setData(
            self._lines_listview.currentIndex(),
            self._line_style_combobox.currentText(),
            Plot1DModel.LineStyleRole,
        )

    def on_change_line_color(self):
        """Callback called when the line color is changed."""
        color = QtWidgets.QColorDialog(self).getColor()
        if not color.isValid():
            return
        rgb_255 = (color.red(), color.green(), color.blue())
        self._line_color_pushbutton.setStyleSheet(f"background-color : rgb{rgb_255}")
        line_color = (rgb_255[0] / 255, rgb_255[1] / 255, rgb_255[2] / 255)
        self._plot_1d_model.setData(
            self._lines_listview.currentIndex(), line_color, Plot1DModel.LineColorRole
        )

    def on_change_line_width(self, width):
        """Callback called when the line width is changed.

        Args:
            width (float): the new line width
        """
        self._plot_1d_model.setData(
            self._lines_listview.currentIndex(), width, Plot1DModel.LineWidthRole
        )

    def on_change_marker_style(self, index):
        """Callback when the ;arker style combobox value is changed.

        Args:
            index (int): the index of the selected marker style item
        """
        self._plot_1d_model.setData(
            self._lines_listview.currentIndex(),
            self._marker_style_combobox.currentText(),
            Plot1DModel.MarkerStyleRole,
        )

    def on_close(self, result):
        """Callback called when the dialog is closed.

        Args:
            result (int): the result of the closing process.
        """
        self._plot_1d_model.unselect_line()

    def on_select_line(self, index):
        """Callback called when a line is selected from the line listview.

        Args:
            index (qtpy.QtCore.QModelIndex): the index of the selected line
        """
        line = self._plot_1d_model.data(index, Plot1DModel.LineRole)
        self._plot_1d_model.select_line(line)
        self._line_style_combobox.setCurrentText(line.get_linestyle())
        self._line_width_doublespinbox.setValue(line.get_linewidth())
        self._marker_style_combobox.setCurrentText(line.get_marker())
        rgb = line.get_color()
        try:
            rgb = rgb.lstrip("#")
            rgb = tuple(int(rgb[i : i + 2], 16) for i in (0, 2, 4))
        except AttributeError:
            rgb = tuple([int(255 * v) for v in rgb])

        self._line_color_pushbutton.setStyleSheet(f"background-color : rgb{rgb}")

    def on_update(self):
        """Update the widgets of the dialog."""
        self._line_style_combobox.clear()
        self._line_style_combobox.addItems(Plot1DModel.line_styles)

        self._marker_style_combobox.clear()
        self._marker_style_combobox.addItems(Plot1DModel.markers)

        self._line_splitter_maximum_offset_doublespinbox.setValue(
            self._plot_1d_model.get_line_splitter_maximum_offset()
        )
