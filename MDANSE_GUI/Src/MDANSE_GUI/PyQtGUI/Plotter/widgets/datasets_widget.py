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

from MDANSE_GUI.PyQtGUI.Plotter.models.data_tree_model import (
    DataTreeItem,
    DataTreeModel,
)


class DatasetsWidget(QtWidgets.QWidget):
    dataset_selected = QtCore.Signal(dict)

    def __init__(self, *args, **kwargs):
        super(DatasetsWidget, self).__init__(*args, **kwargs)

        self._build()

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()

        self._datasets_treeview = QtWidgets.QTreeView()

        main_layout.addWidget(self._datasets_treeview)

        self._selected_dataset_lineedit = QtWidgets.QLineEdit()
        main_layout.addWidget(self._selected_dataset_lineedit)

        self.setLayout(main_layout)

    def get_selected_dataset_axis_info(self):
        model = self._datasets_treeview.model()
        current_index = self._datasets_treeview.currentIndex()
        axis_dataset_info = model.data(current_index, DataTreeModel.AxisInfoRole)
        return axis_dataset_info

    def get_selected_dataset_info(self):
        model = self._datasets_treeview.model()
        current_index = self._datasets_treeview.currentIndex()
        dataset_info = model.data(current_index, DataTreeModel.DatasetInfoRole)
        return dataset_info

    def on_select_dataset(self, index):
        dataset_info = self.get_selected_dataset_info()
        self._selected_dataset_lineedit.setText(dataset_info["path"])
        self.dataset_selected.emit(dataset_info)

    def on_dataset_autocomplete(self):
        selected_dataset_path = self._selected_dataset_lineedit.text()
        datatree_model = self._datasets_treeview.model()
        index = datatree_model.get_index_from_path(selected_dataset_path)
        if not index.isValid():
            return

        self._datasets_treeview.setCurrentIndex(index)

        dataset_info = self.get_selected_dataset_info()
        self.dataset_selected.emit(dataset_info)

    def set_model(self, data_model):
        self._datasets_treeview.setModel(data_model)
        self._datasets_treeview.clicked.connect(self.on_select_dataset)
        if data_model is None:
            return

        datasets = data_model.get_registered_datasets()
        completer = QtWidgets.QCompleter(datasets)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        completer.activated.connect(self.on_dataset_autocomplete)
        self._selected_dataset_lineedit.setCompleter(completer)

    def update(self):
        model = self._datasets_treeview.model()
        if model is None:
            return
        model.layoutChanged.emit()
