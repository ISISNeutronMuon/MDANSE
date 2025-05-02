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
from qtpy.QtCore import QObject, Slot, Signal, QMutex, QModelIndex, Qt, QThread
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE.MolecularDynamics.Trajectory import Trajectory


class LoaderThread(QThread):
    results = Signal(object)

    def __init__(self, parent, filename: str, index: int):
        super().__init__(parent)
        self._filename = filename
        self._target_index = index

    def run(self):
        trajectory = Trajectory(self._filename)
        self.results.emit((trajectory, self._target_index))


class TrajectoryModel(QStandardItemModel):
    """Like GeneralModel, but should implement trajectory
    loading in the background."""

    error = Signal(str)
    all_elements = Signal(object)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._node_numbers = []
        self._trajectory_paths = {}
        self._trajectory_instances = {}
        self._loading_threads = {}
        self._next_number = 0

    @Slot(tuple)
    def append_object(self, input: tuple):
        full_name, label = input
        self.mutex.lock()
        self._node_numbers.append(self._next_number)
        self._trajectory_paths[self._next_number] = full_name
        self._trajectory_instances[self._next_number] = None
        retval = int(self._next_number)
        self.launch_loader(full_name, self._next_number)
        self._next_number += 1
        item = QStandardItem(label)
        item.setData(retval)
        self.appendRow(item)
        self.mutex.unlock()
        self.summarise_items()
        return retval

    def launch_loader(self, filename: str, index: int):
        thread = LoaderThread(None, filename, index)
        thread.results.connect(self.accept_results)
        self._loading_threads[index] = thread
        thread.start()

    def get_trajectory(self, index: int):
        self.mutex.lock()
        result = self._trajectory_instances.get(index)
        self.mutex.unlock()
        return result

    @Slot(object)
    def accept_results(self, result_tuple):
        self.mutex.lock()
        trajectory, index = result_tuple
        self._trajectory_instances[index] = trajectory
        self.mutex.unlock()
        # self._loading_threads[index].wait()

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
        self._trajectory_instances.pop(node_number)
        self._trajectory_paths.pop(node_number)
        self._node_numbers.pop(self._node_numbers.index(node_number))
        if parent is None:
            super().removeRow(row)
        else:
            super().removeRow(row, parent)
        self.mutex.unlock()
        self.summarise_items()
