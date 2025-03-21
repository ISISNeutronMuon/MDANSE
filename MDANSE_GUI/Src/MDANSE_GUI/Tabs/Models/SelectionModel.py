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
import json
import time
from typing import Optional

from MDANSE.Framework.AtomSelector.selection_storage import (
    SelectionStorage,
    SingleEntry,
)
from qtpy.QtCore import QModelIndex, QMutex, QObject, Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel


class SelectionGUIModel(QStandardItemModel):
    """Encapsulates an MDANSE SelectionStorage for GUI access."""

    error = Signal(str)
    all_elements = Signal(object)

    def __init__(self, parent: QObject = None, filename: Optional[str] = None):
        """Load database from file.

        Parameters
        ----------
        source_file : str, optional
            path to a database file.
        parent : QObject, optional
            parent in the Qt object hierarchy
        filename : str, optional
            name of an additional file containing atom selections

        """
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._selection_storage = SelectionStorage(filename=filename)
        self.build_model_from_storage(self._selection_storage)

    def build_model_from_storage(self, storage: SelectionStorage):
        """Initialise the GUI model from an MDANSE storage instance.

        Parameters
        ----------
        storage : SelectionStorage
            an instance of MDANSE SelectionStorage

        """
        self.clear()
        for entry in storage._named_entries.values():
            self.add_single_selection(entry)
        for entry in storage._unnamed_entries:
            self.add_single_selection(entry)

    def column_headers(self) -> dict[str, int]:
        """Get the mapping of data field names to column numbers.

        Returns
        -------
        dict[str, int]
            A dictionary of column numbers for each data field name

        """
        return {
            self.headerData(col_number, Qt.Orientation.Horizontal): col_number
            for col_number in range(len(self.columnCount()))
        }

    def add_single_selection(self, entry: SingleEntry):
        """Add an entry to be displayed in the GUI via the model.

        Parameters
        ----------
        entry : SingleEntry
            a SingleEntry object from the MDANSE selection storage

        """
        column_dict = self.column_headers()
        column_headers = list(column_dict.keys())
        for field in entry.data_fields:
            if field not in column_headers:
                column_headers.add(field)
        self.setHorizontalHeaderLabels(column_headers)
        new_column_dict = self.column_headers()
        row = len(new_column_dict) * [None]
        for field in new_column_dict:
            data_entry = QStandardItem(json.dumps(getattr(entry, field, "")))
            data_entry.setEditable(False)
            row[new_column_dict[field]] = data_entry
        self.appendRow(row)
