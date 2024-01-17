from qtpy.QtCore import QObject, Slot, Signal, QMutex
from qtpy.QtGui import QStandardItemModel, QStandardItem


class GeneralModel(QStandardItemModel):
    """Meant to be used with DoublePanel, GeneralView
    and ItemVisualiser. It stores elements and emits
    them to the ItemVisualiser."""

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
        return retval
