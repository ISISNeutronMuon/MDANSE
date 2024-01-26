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

from qtpy import QtCore, QtWidgets

from MDANSE_GUI.PyQtGUI.pygenplot.dialogs.inspect_data_dialog import InspectDataDialog
from MDANSE_GUI.PyQtGUI.pygenplot.models.data_tree_model import DataItem, DataTreeModel


class DataWidget(QtWidgets.QWidget):
    dataset_selected = QtCore.Signal(dict)

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(DataWidget, self).__init__(*args, **kwargs)

        self._build()

    def _build(self):
        """Build the widget."""
        main_layout = QtWidgets.QVBoxLayout()

        self._data_treeview = QtWidgets.QTreeView()
        self._data_treeview.setHeaderHidden(True)
        self._data_treeview.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        data_model = DataTreeModel(self)
        self._data_treeview.setModel(data_model)

        main_layout.addWidget(self._data_treeview)

        self._selected_dataset_lineedit = QtWidgets.QLineEdit()
        main_layout.addWidget(self._selected_dataset_lineedit)

        self.setLayout(main_layout)

        self._data_treeview.clicked.connect(self.on_select_tree_item)
        self._data_treeview.customContextMenuRequested.connect(
            self.on_open_contextual_menu
        )

    def eventFilter(self, source, event):
        """Event filter for the widget.

        Args:
            source (qtpy.QtWidgets.QWidget): the widget triggering the event.
            event (qtpy.QtCore.QEvent): the event
        """
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Delete:
                if source == self._data_treeview:
                    current_index = self._data_treeview.currentIndex()
                    self._data_treeview.model().removeRow(
                        current_index.row(), current_index.parent()
                    )
        return super(DataWidget, self).eventFilter(source, event)

    def get_selected_dataset_axis_info(self):
        """Return the axis info of a selected widget.

        Returns:
            list of dict: the axis info
        """
        model = self._data_treeview.model()
        current_index = self._data_treeview.currentIndex()
        axis_dataset_info = model.data(current_index, DataTreeModel.AxisInfoRole)
        return axis_dataset_info

    def get_selected_dataset_info(self):
        """Returns the info about a selected dataset.

        Returns:
            dict: the information
        """
        model = self._data_treeview.model()
        current_index = self._data_treeview.currentIndex()
        dataset_info = model.data(current_index, DataTreeModel.DatasetInfoRole)
        return dataset_info

    def model(self):
        """Returns the model underlying the widget.

        Args:
            pygenplot.models.data_tree_model.DataTreeModel: the model
        """
        return self._data_treeview.model()

    def on_dataset_autocomplete(self):
        """Callback called when an autocmpletion item has been selected."""
        selected_dataset_path = self._selected_dataset_lineedit.text()
        datatree_model = self._data_treeview.model()
        index = datatree_model.get_index_from_path(selected_dataset_path)
        if not index.isValid():
            return

        self._data_treeview.setCurrentIndex(index)

        dataset_info = self.get_selected_dataset_info()
        self.dataset_selected.emit(dataset_info)

    def on_display_data(self):
        """Callback called when the user clicks on the Display data item of the contextual menu of data tree."""
        dataset_info = self.get_selected_dataset_info()
        dlg = InspectDataDialog(dataset_info, self)
        dlg.show()

    def on_open_contextual_menu(self, point):
        """Callback called when the user right-click on the data tree view.

        Args:
            point (qtpy.QtCore.QPoint): the point of click
        """
        current_index = self._data_treeview.currentIndex()
        node = current_index.internalPointer()
        if node is None or node.is_group():
            return

        menu = QtWidgets.QMenu(self)
        copy_to_clipboard_action = menu.addAction("Display data")
        copy_to_clipboard_action.triggered.connect(self.on_display_data)
        menu.exec(self._data_treeview.mapToGlobal(point))

    def on_select_tree_item(self, index):
        """Callback called when an item of the data tree has been selected.

        Args:
            index (qtpy.QtCore.QModelIndex): the index of the item
        """
        node = index.internalPointer()
        if isinstance(node, DataItem):
            datasets = []
            node.get_registered_datasets(datasets)
            datasets.sort()
            completer = QtWidgets.QCompleter(datasets)
            completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
            completer.activated.connect(self.on_dataset_autocomplete)
            self._selected_dataset_lineedit.setCompleter(completer)
        else:
            if node.is_group():
                return
            else:
                dataset_info = self.get_selected_dataset_info()
                self._selected_dataset_lineedit.setText(dataset_info["path"])
                self.dataset_selected.emit(dataset_info)