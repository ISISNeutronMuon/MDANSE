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
from __future__ import annotations

from qtpy.QtCore import QModelIndex, QMutex, QObject, Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel


class GeneralModel(QStandardItemModel):
    """Meant to be used with DoublePanel, GeneralView
    and ItemVisualiser. It stores elements and emits
    them to the ItemVisualiser."""

    error = Signal(str)
    all_elements = Signal(object)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._node_numbers = []
        self._nodes = {}
        self._next_number = 0

    @Slot(tuple)
    def append_object(self, input: tuple):
        thing, label = input
        self.mutex.lock()
        self._nodes[self._next_number] = thing
        self._node_numbers.append(self._next_number)
        retval = int(self._next_number)
        self._next_number += 1
        item = QStandardItem(label)
        item.setData(retval)
        self.appendRow(item)
        self.mutex.unlock()
        self.summarise_items()
        return retval

    @Slot(tuple)
    def append_object_and_embed(self, input: tuple):
        thing, label = input
        self.mutex.lock()
        self._nodes[self._next_number] = thing
        self._node_numbers.append(self._next_number)
        retval = int(self._next_number)
        self._next_number += 1
        item = QStandardItem(label)
        item.setData(retval)
        thing._list_item = item
        thing._model_index = retval
        self.appendRow(item)
        self.mutex.unlock()
        self.summarise_items()
        return retval

    def summarise_items(self):
        result = []
        self.mutex.lock()
        for nrow in range(self.rowCount()):
            index = self.index(nrow, 0)
            item = self.itemFromIndex(index)
            result.append([item.text(), item.data()])
        self.mutex.unlock()
        self.all_elements.emit(result)

    def removeRow(self, row: int, parent: QModelIndex = None):
        self.mutex.lock()
        try:
            node_number = self.item(row).data()
        except AttributeError:
            return
        self._nodes.pop(node_number)
        self._node_numbers.pop(self._node_numbers.index(node_number))
        if parent is None:
            super().removeRow(row)
        else:
            super().removeRow(row, parent)
        self.mutex.unlock()
        self.summarise_items()
