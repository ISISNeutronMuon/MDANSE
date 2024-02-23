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

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from MDANSE_GUI.Plotter.dialogs.plot_2d_general_settings_dialog import (
    Plot2DGeneralSettingsDialog,
)
from MDANSE_GUI.Plotter.dialogs.plot_2d_image_settings_dialog import (
    Plot2DImageSettingsDialog,
)
from MDANSE_GUI.Plotter.models.plot_2d_model import (
    Plot2DModel,
    Plot2DModelError,
)
from MDANSE_GUI.Plotter.dialogs.cross_viewer_dialog import CrossViewerDialog


class Plot2DWidget(QtWidgets.QWidget):
    def __init__(
        self, plot_type, x_data_info, y_data_info, z_data_info, *args, **kwargs
    ):
        super(Plot2DWidget, self).__init__(*args, **kwargs)

        self._plot_2d_model = None

        self._plot_type = plot_type

        self._general_settings_dialog = None
        self._image_settings_dialog = None
        self._cross_viewer_dialog = None

        self._build()

        self._plot(x_data_info, y_data_info, z_data_info)

    def _build(self):
        """ """
        self._figure = Figure()
        canvas = FigureCanvasQTAgg(self._figure)
        canvas.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        canvas.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        canvas.customContextMenuRequested.connect(self.on_open_contextual_menu)
        canvas.setFocus()
        self._toolbar = NavigationToolbar2QT(canvas, self)

        self._figure.add_subplot(111)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(canvas, 1)
        main_layout.addWidget(self._toolbar)

        self.setLayout(main_layout)

    def _plot(self, x_data_info, y_data_info, z_data_info):
        """ """

        try:
            self._plot_2d_model = Plot2DModel(
                self._figure, x_data_info, y_data_info, z_data_info
            )
        except Plot2DModelError as e:
            print(str(e), ["main", "popup"], "error")
            return

    def close(self):
        if self._general_settings_dialog is not None:
            self._general_settings_dialog.close()

        if self._image_settings_dialog is not None:
            self._image_settings_dialog.close()

        if self._cross_viewer_dialog is not None:
            self._cross_viewer_dialog.close()

    def get_plot_type(self):
        """ """
        return self._plot_type

    def on_export_data(self):
        """ """
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save data", "", "Data file (*.txt)"
        )
        if not filename:
            return

        self._plot_2d_model.export_data(filename)

    def on_open_contextual_menu(self, event):
        menu = QtWidgets.QMenu(self)
        plot_settings_action = menu.addAction("General settings")
        plot_settings_action.triggered.connect(self.on_open_general_settings_dialog)
        image_settings_action = menu.addAction("Image settings")
        image_settings_action.triggered.connect(self.on_open_image_settings_dialog)
        menu.addSeparator()
        cross_viewer_action = menu.addAction("Cross viewer")
        cross_viewer_action.triggered.connect(self.on_open_cross_viewer_dialog)
        menu.addSeparator()
        export_action = menu.addAction("Export data")
        export_action.triggered.connect(self.on_export_data)
        menu.exec(self._figure.canvas.mapToGlobal(event))

    def on_open_general_settings_dialog(self):
        if self._general_settings_dialog is None:
            self._general_settings_dialog = Plot2DGeneralSettingsDialog(
                self._plot_2d_model, self
            )
        self._general_settings_dialog.show()

    def on_open_image_settings_dialog(self):
        if self._image_settings_dialog is None:
            self._image_settings_dialog = Plot2DImageSettingsDialog(
                self._plot_2d_model, self
            )
        self._image_settings_dialog.show()

    def on_open_cross_viewer_dialog(self):
        if self._cross_viewer_dialog is None:
            self._cross_viewer_dialog = CrossViewerDialog(self._plot_2d_model, self)
        self._cross_viewer_dialog.show()
