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
from qtpy import QtCore, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from MDANSE.MLogging import LOG

from MDANSE_GUI.Plotter.dialogs.data_viewer_1d_dialog import (
    DataViewer1DDialog,
)
from MDANSE_GUI.Plotter.dialogs.plot_1d_axis_settings_dialog import (
    Plot1DAxisSettingsDialog,
)
from MDANSE_GUI.Plotter.dialogs.plot_1d_general_settings_dialog import (
    Plot1DGeneralSettingsDialog,
)
from MDANSE_GUI.Plotter.dialogs.plot_1d_lines_settings_dialog import (
    Plot1DLinesSettingsDialog,
)
from MDANSE_GUI.Plotter.models.plot_1d_model import (
    Plot1DModel,
    Plot1DModelError,
)


class Plot1DWidget(QtWidgets.QWidget):
    def __init__(self, plot_type, x_data_info, *args, **kwargs):
        """Constructor.

        Args:
            plot_type(str): the plot type
            x_data_info (dict): te information about the X axis of the 1D plot
        """
        super(Plot1DWidget, self).__init__(*args, **kwargs)

        self._plot_type = plot_type

        self._selected_line = None

        self._axis_settings_dialog = None
        self._lines_settings_dialog = None
        self._general_settings_dialog = None
        self._data_viewer_1d_dialog = None

        self._build()

        self._plot_1d_model = Plot1DModel(self._figure, x_data_info, self)

    def _build(self):
        """Build the widget."""
        self._figure = Figure()
        canvas = FigureCanvasQTAgg(self._figure)
        canvas.setFocusPolicy(QtCore.Qt.FocusPolicy.ClickFocus)
        canvas.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        canvas.customContextMenuRequested.connect(self.on_open_contextual_menu)
        canvas.setFocus()
        self._toolbar = NavigationToolbar2QT(canvas, self)

        self._figure.add_subplot(111, picker=True)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(canvas, 1)
        main_layout.addWidget(self._toolbar)

        self.setLayout(main_layout)

        canvas.mpl_connect("pick_event", self.on_pick_line)
        canvas.mpl_connect("key_press_event", self.on_key_press)

    def add_line(self, y_data_info):
        """Add a line to the plot.

        Args:
            y_data_info (dict): the information about the line to plot
        """
        try:
            self._plot_1d_model.add_line(y_data_info)
        except Plot1DModelError as e:
            LOG.error(f'{str(e)}, {"main", "popup"}, {"error"}')
            return

    def close(self):
        """Close the widget."""
        self.on_close_axis_settings_dialog()

        self.on_close_general_settings_dialog()

        self.on_close_lines_settings_dialog()

        self.on_close_data_viewer_1d_dialog()

    def get_plot_1d_model(self):
        """Returns the model underlying the widget.

        Returns:
            Plotter.models.plot_1d_model.Plot1DModel: the 1D data model
        """
        return self._plot_1d_model

    def get_plot_type(self):
        """Returns the plot type.

        Returns:
            str: the plot type
        """
        return self._plot_type

    def on_clear_plot(self):
        """Callback called zhen the clear item of the contextual menu is clicked. Clear the plot."""
        self._plot_1d_model.clear()

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

    def on_close_lines_settings_dialog(self):
        """Callback called when the lines settings dialog is closed."""
        if self._lines_settings_dialog is not None:
            self._lines_settings_dialog.close()
        self._lines_settings_dialog = None

    def on_close_data_viewer_1d_dialog(self):
        """Callback called when the data viewer dialog is closed."""
        if self._data_viewer_1d_dialog is not None:
            self._data_viewer_1d_dialog.close()
        self._data_viewer_1d_dialog = None

    def on_key_press(self, event):
        """Callback called when a key is pressed on the plot.

        Args:
            event (matplotlib.backend_bases.KeyEvent): the keypress event
        """
        if event.key == "delete":
            selected_line_index = self._plot_1d_model.get_selected_line_index()
            if selected_line_index is not None:
                choice = QtWidgets.QMessageBox.question(
                    self,
                    "Delete line",
                    "Do you really want to delete this line ?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                )

                if choice == QtWidgets.QMessageBox.StandardButton.No:
                    return False

                self._plot_1d_model.removeRow(selected_line_index)

    def on_open_axis_settings_dialog(self):
        """Callback called when the axis settings dialog is opened."""
        if self._axis_settings_dialog is None:
            self._axis_settings_dialog = Plot1DAxisSettingsDialog(
                self._plot_1d_model, self
            )
        self._axis_settings_dialog.show()

    def on_open_contextual_menu(self, event):
        """Opens the contextual menu.

        Args:
            event (atpy.QtCore.QEvent): the event
        """
        menu = QtWidgets.QMenu(self)
        plot_settings_action = menu.addAction("General settings")
        plot_settings_action.triggered.connect(self.on_open_general_settings_dialog)
        axis_settings_action = menu.addAction("Axis settings")
        axis_settings_action.triggered.connect(self.on_open_axis_settings_dialog)
        lines_settings_action = menu.addAction("Lines settings")
        lines_settings_action.triggered.connect(self.on_open_lines_settings_dialog)
        menu.addSeparator()
        clear_action = menu.addAction("Clear")
        clear_action.triggered.connect(self.on_clear_plot)
        menu.addSeparator()
        view_data_action = menu.addAction("View data")
        view_data_action.triggered.connect(self.on_open_view_1d_data_dialog)
        menu.exec(self._figure.canvas.mapToGlobal(event))

    def on_open_general_settings_dialog(self):
        """Callback called when the general settings dialog is opened."""
        if self._general_settings_dialog is None:
            self._general_settings_dialog = Plot1DGeneralSettingsDialog(
                self._plot_1d_model, self
            )
        self._general_settings_dialog.show()

    def on_open_lines_settings_dialog(self):
        """Callback called when the lines settings dialog is opened."""
        if self._lines_settings_dialog is None:
            self._lines_settings_dialog = Plot1DLinesSettingsDialog(
                self._plot_1d_model, self
            )
        self._lines_settings_dialog.show()

    def on_open_view_1d_data_dialog(self):
        """Callback called when the data viewer dialog is opened."""
        if self._data_viewer_1d_dialog is None:
            self._data_viewer_1d_dialog = DataViewer1DDialog(self._plot_1d_model, self)
        self._data_viewer_1d_dialog.show()

    def on_pick_line(self, event):
        """Callback when the mouse is pressed over the plot.

        Args:
            event (matplotlib.backend_bases.MouseEvent): the mouse press event
        """
        if event.mouseevent.button == 3:
            return

        if event.artist == self._figure.axes[0]:
            self._plot_1d_model.unselect_line()
        else:
            self._plot_1d_model.select_line(event.artist)

    def set_plot_1d_model(self, model):
        """Set the 1D data model.

        Args:
            model (Plotter.models.plot_1d_model.Plot1DModel): the 1D data model
        """
        self._plot_1d_model = model
