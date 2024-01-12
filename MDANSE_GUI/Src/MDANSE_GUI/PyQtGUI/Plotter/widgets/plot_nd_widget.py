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

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from MDANSE_GUI.PyQtGUI.Plotter.dialogs.cross_viewer_dialog import CrossViewerDialog
from MDANSE_GUI.PyQtGUI.Plotter.dialogs.data_viewer_nd_dialog import (
    DataViewerNDDialog,
)
from MDANSE_GUI.PyQtGUI.Plotter.dialogs.slice_viewer_dialog import SliceViewerDialog
from MDANSE_GUI.PyQtGUI.Plotter.dialogs.plot_nd_axis_settings_dialog import (
    PlotNDAxisSettingsDialog,
)
from MDANSE_GUI.PyQtGUI.Plotter.dialogs.plot_nd_general_settings_dialog import (
    PlotNDGeneralSettingsDialog,
)
from MDANSE_GUI.PyQtGUI.Plotter.dialogs.plot_nd_image_settings_dialog import (
    PlotNDImageSettingsDialog,
)
from MDANSE_GUI.PyQtGUI.Plotter.models.plot_nd_model import PlotNDModel


class PlotNDWidget(QtWidgets.QWidget):
    def __init__(self, plot_type, axis_info, data_info, *args, **kwargs):
        """Constructor.

        Args:
            plot_type (str): the plot type
            axis_info (list of dict): the informations about each axis of the ND data
            data_info (dict): the information about the ND data
        """
        super(PlotNDWidget, self).__init__(*args, **kwargs)

        self._plot_nd_model = None

        self._plot_type = plot_type

        self._general_settings_dialog = None
        self._axis_settings_dialog = None
        self._image_settings_dialog = None
        self._cross_viewer_dialog = None
        self._slice_viewer_dialog = None
        self._data_viewer_nd_dialog = None

        self._build()

        self._plot_nd_model = PlotNDModel(self._figure, axis_info, data_info)

    def _build(self):
        """Build the widget."""
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

    def close(self):
        """Close the widget."""
        self.on_close_axis_settings_dialog()

        self.on_close_general_settings_dialog()

        self.on_close_image_settings_dialog()

        self.on_close_cross_viewer_dialog()

        self.on_close_slice_viewer_dialog()

        self.on_close_data_viewer_nd_dialog()

    def get_plot_type(self):
        """Returns the plot type.

        Returns:
            str: the plot type
        """
        return self._plot_type

    def on_close_axis_settings_dialog(self):
        """Callback called when the axis settings dialog is closed."""
        if self._axis_settings_dialog is not None:
            self._axis_settings_dialog.close()
        self._axis_settings_dialog = None

    def on_close_general_settings_dialog(self):
        """Callback called when the general settings dialog is closed."""
        if self._general_settings_dialog is not None:
            self._general_settings_dialog.close()
        self._general_settings_dialog = None

    def on_close_image_settings_dialog(self):
        """Callback called when the image settings dialog is closed."""
        if self._image_settings_dialog is not None:
            self._image_settings_dialog.close()
        self._image_settings_dialog = None

    def on_close_cross_viewer_dialog(self):
        """Callback called when the cross viewer dialog is closed."""
        if self._cross_viewer_dialog is not None:
            self._cross_viewer_dialog.close()
        self._cross_viewer_dialog = None

    def on_close_data_viewer_nd_dialog(self):
        """Callback called when the data viewer dialog is closed."""
        if self._data_viewer_nd_dialog is not None:
            self._data_viewer_nd_dialog.close()
        self._data_viewer_nd_dialog = None

    def on_close_slice_viewer_dialog(self):
        """Callback called when the slice viewer dialog is closed."""
        if self._slice_viewer_dialog is not None:
            self._slice_viewer_dialog.close()
        self._slice_viewer_dialog = None

    def on_open_contextual_menu(self, event):
        """Open the contextual menu.

        Args:
            event (qtpy.QtCore.QEvent): the event
        """
        menu = QtWidgets.QMenu(self)
        plot_settings_action = menu.addAction("General settings")
        plot_settings_action.triggered.connect(self.on_open_general_settings_dialog)
        axis_settings_action = menu.addAction("Axis settings")
        axis_settings_action.triggered.connect(self.on_open_axis_settings_dialog)
        image_settings_action = menu.addAction("Image settings")
        image_settings_action.triggered.connect(self.on_open_image_settings_dialog)
        menu.addSeparator()
        view_data_action = menu.addAction("View data")
        view_data_action.triggered.connect(self.on_open_view_nd_data_dialog)
        menu.addSeparator()
        cross_viewer_action = menu.addAction("Cross viewer")
        cross_viewer_action.triggered.connect(self.on_open_cross_viewer_dialog)
        slice_viewer_action = menu.addAction("Slice viewer")
        slice_viewer_action.triggered.connect(self.on_open_slice_viewer_dialog)
        menu.exec(self._figure.canvas.mapToGlobal(event))

    def on_open_axis_settings_dialog(self):
        """Callback called to open the axis settings dialog."""
        if self._axis_settings_dialog is None:
            self._axis_settings_dialog = PlotNDAxisSettingsDialog(
                self._plot_nd_model, self
            )
        self._axis_settings_dialog.show()

    def on_open_general_settings_dialog(self):
        """Callback called to open the general settings dialog."""
        if self._general_settings_dialog is None:
            self._general_settings_dialog = PlotNDGeneralSettingsDialog(
                self._plot_nd_model, self
            )
        self._general_settings_dialog.show()

    def on_open_image_settings_dialog(self):
        """Callback called to open the image settings dialog."""
        if self._image_settings_dialog is None:
            self._image_settings_dialog = PlotNDImageSettingsDialog(
                self._plot_nd_model, self
            )
        self._image_settings_dialog.show()

    def on_open_cross_viewer_dialog(self):
        """Callback called to open the cross viewer dialog."""
        if self._cross_viewer_dialog is None:
            self._cross_viewer_dialog = CrossViewerDialog(self._plot_nd_model, self)
        self._cross_viewer_dialog.show()

    def on_open_slice_viewer_dialog(self):
        """Callback called to open the slice viewer dialog."""
        if self._slice_viewer_dialog is None:
            self._slice_viewer_dialog = SliceViewerDialog(self._plot_nd_model, self)
        self._slice_viewer_dialog.show()

    def on_open_view_nd_data_dialog(self):
        """Callback called to open the ND data viewer dialog."""
        if self._data_viewer_nd_dialog is None:
            self._data_viewer_nd_dialog = DataViewerNDDialog(self._plot_nd_model, self)
        self._data_viewer_nd_dialog.show()
