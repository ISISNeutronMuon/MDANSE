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

from MDANSE_GUI.PyQtGUI.Plotter.views.table_views import QTableViewWithoutRightClick


class DataViewer1DDialog(QtWidgets.QDialog):
    def __init__(self, plot_1d_model, *args, **kwargs):
        """Constructor.

        Args:
            plot_1d_model (Plotter.models.plot_1d_model.Plot1DModel): the 1D data model
        """
        super(DataViewer1DDialog, self).__init__(*args, **kwargs)

        self._plot_1d_model = plot_1d_model

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

        self.setLayout(main_layout)

        self._plot_1d_model.model_updated.connect(self.on_update_table)

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

        return super(DataViewer1DDialog, self).eventFilter(source, event)

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

        copied_data = [
            ",".join(
                [
                    model.headerData(c, QtCore.Qt.Orientation.Horizontal)
                    for c in selected_columns
                ]
            )
        ]
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
        x_data = self._plot_1d_model.get_x_axis_data()
        y_data = self._plot_1d_model.get_y_axis_data()

        x_data_labels = self._plot_1d_model.get_x_axis_label()
        y_data_labels = self._plot_1d_model.get_line_full_names()

        column_names = [x_data_labels] + y_data_labels

        model = QtGui.QStandardItemModel()
        model.appendColumn([QtGui.QStandardItem(str(x)) for x in x_data])
        for yd in y_data:
            model.appendColumn([QtGui.QStandardItem(str(y)) for y in yd])
        model.setHorizontalHeaderLabels(column_names)

        self._data_table_view.setModel(model)
