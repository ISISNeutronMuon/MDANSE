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

from MDANSE_GUI.Plotter.dialogs.units_editor_dialog import UnitsEditorDialog


class ActionsWidget(QtWidgets.QWidget):
    units_updated = QtCore.Signal()

    plot_in_new_figure = QtCore.Signal(str)
    plot_in_current_figure = QtCore.Signal(str)

    _plot_types = {1: "Line", 2: "Image"}

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(ActionsWidget, self).__init__(*args, **kwargs)

        self._units_editor_dialog = None

        self._build()

        self.reset()

    def _build(self):
        """Build the widget."""
        main_layout = QtWidgets.QVBoxLayout()
        self._edit_units_pushbutton = QtWidgets.QPushButton("Edit units")
        main_layout.addWidget(self._edit_units_pushbutton)
        hlayout = QtWidgets.QHBoxLayout()
        self._new_plot_pushbutton = QtWidgets.QPushButton("Plot in new figure")
        self._current_plot_pushbutton = QtWidgets.QPushButton("Plot in current figure")
        hlayout.addWidget(self._new_plot_pushbutton)
        hlayout.addWidget(self._current_plot_pushbutton)
        main_layout.addLayout(hlayout)
        main_layout.addStretch()
        self.setLayout(main_layout)

        self.reset()

        self._edit_units_pushbutton.clicked.connect(self.on_open_units_editor)
        self._new_plot_pushbutton.clicked.connect(self.on_plot_in_new_figure)
        self._current_plot_pushbutton.clicked.connect(self.on_plot_in_current_figure)

    def on_open_units_editor(self):
        """Callback called when open units editor button is clicked."""
        if self._units_editor_dialog is None:
            self._units_editor_dialog = UnitsEditorDialog(self)
            self._units_editor_dialog.accepted.connect(
                lambda: self.units_updated.emit()
            )
        self._units_editor_dialog.show()

    def on_plot_in_current_figure(self):
        """Callback called when the plot in current figure button is clicked."""
        if self._ndim is None:
            return
        plot_type = ActionsWidget._plot_types[self._ndim]
        self.plot_in_current_figure.emit(plot_type)

    def on_plot_in_new_figure(self):
        """Callback called when the plot in new figure button is clicked."""
        if self._ndim is None:
            return
        plot_type = ActionsWidget._plot_types.get(self._ndim, "2D Slice")
        self.plot_in_new_figure.emit(plot_type)

    def reset(self):
        """Reset the widget."""
        self._ndim = None
        self._new_plot_pushbutton.setDisabled(True)
        self._current_plot_pushbutton.setDisabled(True)

    def set_data(self, data):
        """Update the widget wit new data.

        Args:
            data (array): the data
        """
        self._ndim = data.ndim
        self._new_plot_pushbutton.setDisabled(False)
        self._current_plot_pushbutton.setDisabled(self._ndim > 1)
