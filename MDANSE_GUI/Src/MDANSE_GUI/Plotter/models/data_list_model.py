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

import os

from qtpy import QtCore

<<<<<<<< HEAD:MDANSE_GUI/Src/MDANSE_GUI/Plotter/models/data_list_model.py
from MDANSE_GUI.Plotter.models.data_tree_model import DATA_MODELS
========
from MDANSE_GUI.pygenplot.models.data_tree_model import DATA_MODELS
>>>>>>>> a3e31864e3d7a47375ecf27c20e78ea49e783dc8:MDANSE_GUI/Src/MDANSE_GUI/pygenplot/models/data_list_model.py


class DataListModel(QtCore.QAbstractListModel):
    DataModelRole = QtCore.Qt.ItemDataRole.UserRole

    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

        self._data_models = []

    def add_data(self, filename):
        loaded_filenames = [
            data_model.get_filename() for data_model in self._data_models
        ]
        if filename in loaded_filenames:
            return

        extension = os.path.splitext(filename)[1]
        try:
            data_model_class = DATA_MODELS[extension]
        except KeyError:
            print("Unknown file extension")

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        data_model = data_model_class(filename, self)
        self._data_models.append(data_model)
        self.endInsertRows()

    def data(self, index, role):
        """Return the data for a given index and role.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index
            role (int): the role

        Returns:
            any: the data
        """
        row = index.row()
        data_model = self._data_models[row]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return data_model.get_basename()

        elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
            return data_model.get_filename()

        elif role == DataListModel.DataModelRole:
            return data_model

        else:
            return QtCore.QVariant()

    def removeRow(self, row, parent):
        """Remove a row from the model.

        Args:
            row (int): the index of the row to be removed
            parent (PyQt5.QtCore.QModelIndex): the parent

        Returns:
            bool: True if the removal was successful
        """
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        self._data_models[row].deleteLater()
        del self._data_models[row]
        self.endRemoveRows()

        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Return the number of numors stored in the model.

        Args:
            parent (PyQt5.QtCore.QObject): the parent object

        Returns:
            int: the numner of numors stored in the model
        """
        return len(self._data_models)
