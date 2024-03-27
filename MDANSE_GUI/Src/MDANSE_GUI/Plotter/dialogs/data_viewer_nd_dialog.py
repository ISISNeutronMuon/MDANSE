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
# Copyright (C)  Institut Laue Langevin 2023-now
# Authors:    Eric Pellegrini

from qtpy import QtCore, QtGui, QtWidgets

from MDANSE_GUI.Plotter.views.table_views import QTableViewWithoutRightClick


class DataViewerNDDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, *args, **kwargs):
        """Constructor.

        Args:
            plot_nd_model (Plotter.models.plot_nd_model.PlotNDModel): the ND data model
        """
        super(DataViewerNDDialog, self).__init__(*args, **kwargs)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.setWindowTitle("Data viewer")

        self.resize(400, 400)

        self.on_update_table()

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        self._data_table_view = QTableViewWithoutRightClick()
        self._data_table_view.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._data_table_view.customContextMenuRequested.connect(
            self.on_open_contextual_menu
        )
        self._data_table_view.installEventFilter(self)
        main_layout.addWidget(self._data_table_view)

        hlayout = QtWidgets.QHBoxLayout()
        self._add_horizontal_header = QtWidgets.QCheckBox("Add horizontal header")
        self._add_vertical_header = QtWidgets.QCheckBox("Add vertical header")
        hlayout.addWidget(self._add_horizontal_header)
        hlayout.addWidget(self._add_vertical_header)
        main_layout.addLayout(hlayout)

        self.setLayout(main_layout)

        self._plot_nd_model.model_updated.connect(self.on_update_table)
        self._add_horizontal_header.clicked.connect(self.on_update_table)
        self._add_vertical_header.clicked.connect(self.on_update_table)

    def eventFilter(self, source, event):
        """Even filter for the dialog.

        Args:
            source (qtpy.QtWidgets.Qwidget): the widget triggering the event
            event (qtpy.QtCore.QEvent): the event
        """
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.matches(QtGui.QKeySequence.StandardKey.Copy):
                self.on_copy_to_clipboard()
                return True

        return super(DataViewerNDDialog, self).eventFilter(source, event)

    def on_copy_to_clipboard(self):
        """Callback called when some data has been copied to the clipboard."""
        model = self._data_table_view.model()
        selection_model = self._data_table_view.selectionModel()

        selected_columns = set()
        for data_range in selection_model.selection():
            for i in range(data_range.top(), data_range.bottom() + 1):
                for j in range(data_range.left(), data_range.right() + 1):
                    selected_columns.add(j)
        selected_columns = sorted(selected_columns)

        copied_data = []
        for data_range in selection_model.selection():
            for i in range(data_range.top(), data_range.bottom() + 1):
                line = []
                for j in selected_columns:
                    if j in range(data_range.left(), data_range.right() + 1):
                        value = model.data(
                            model.index(i, j), QtCore.Qt.ItemDataRole.DisplayRole
                        )
                    else:
                        value = ""
                    line.append(value)
                line = ",".join(line)
                copied_data.append(line)

        copied_data = "\n".join(copied_data)

        QtWidgets.QApplication.clipboard().setText(copied_data)

    def on_open_contextual_menu(self, point):
        """Callback called when the contextual menu is opened by right-clicking on the data.

        Args:
            point (qtpy.QtCore.QPoint): the point of click
        """
        menu = QtWidgets.QMenu(self)
        copy_to_clipboard_action = menu.addAction("Copy to clipboard")
        copy_to_clipboard_action.triggered.connect(self.on_copy_to_clipboard)
        menu.exec(self._data_table_view.mapToGlobal(point))

    def on_update_table(self):
        """Update the table with the data."""
        x_data = self._plot_nd_model.get_x_axis_data()
        y_data = self._plot_nd_model.get_y_axis_data()
        z_data = self._plot_nd_model.get_data()

        model = QtGui.QStandardItemModel()
        for row in z_data:
            model.appendRow([QtGui.QStandardItem(str(c)) for c in row])

        if self._add_horizontal_header.isChecked():
            model.setHorizontalHeaderLabels([str(y) for y in y_data])

        if self._add_vertical_header.isChecked():
            model.setVerticalHeaderLabels([str(x) for x in x_data])

        self._data_table_view.setModel(model)
