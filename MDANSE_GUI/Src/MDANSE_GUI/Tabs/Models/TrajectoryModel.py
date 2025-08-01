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

import itertools

from qtpy.QtCore import (
    QDeadlineTimer,
    QModelIndex,
    QMutex,
    QObject,
    Qt,
    QThread,
    Signal,
    Slot,
)
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class LoaderThread(QThread):
    results = Signal(object)

    def __init__(
        self,
        parent,
        filename: str,
        index: int,
        *,
        display_item: QStandardItem | None = None,
        target_label: str | None = None,
    ):
        super().__init__(parent)
        self._filename = filename
        self._target_index = index
        self._display_item = display_item
        self._target_label = target_label

    def run(self):
        trajectory = Trajectory(self._filename)
        self.results.emit((trajectory, self._target_index))
        if self._display_item is not None and self._target_label is not None:
            self._display_item.setData(
                self._target_label, role=Qt.ItemDataRole.DisplayRole
            )


class TrajectoryModel(QStandardItemModel):
    """Like GeneralModel, but should implement trajectory
    loading in the background."""

    error = Signal(str)
    all_elements = Signal(object)
    finished_loading = Signal(int)
    free_name = Signal(str)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._node_numbers = []
        self._trajectory_paths = {}
        self._trajectory_instances = {}
        self._loading_threads = {}
        self._next_number = itertools.count()

    @Slot(tuple)
    def append_object(self, input: tuple) -> int:
        full_name, label = input
        retval = next(self._next_number)
        self._node_numbers.append(retval)
        self._trajectory_paths[retval] = full_name
        self._trajectory_instances[retval] = None
        item = QStandardItem(f"Loading {label}...")
        item.setData(retval)
        self.appendRow(item)
        self.launch_loader(full_name, retval, display_item=item, target_label=label)
        return retval

    def launch_loader(
        self,
        filename: str,
        index: int,
        display_item: QStandardItem | None = None,
        target_label: str | None = None,
    ) -> None:
        thread = LoaderThread(
            None, filename, index, display_item=display_item, target_label=target_label
        )
        thread.results.connect(self.accept_results)
        self._loading_threads[index] = thread
        thread.start()

    def get_trajectory(self, index: int) -> None | str | Trajectory:
        result = None
        if index not in self._loading_threads:
            LOG.info("Requesting a missing trajectory with index %s", index)
            return result
        if index not in self._trajectory_instances:
            return f"Loading trajectory {self._trajectory_paths[index]}"
        return self._trajectory_instances[index]

    @Slot(object)
    def accept_results(self, result_tuple) -> None:
        trajectory, index = result_tuple
        if index not in self._trajectory_instances:
            return
        self._trajectory_instances[index] = trajectory
        self.finished_loading.emit(index)
        # self._loading_threads[index].wait()

    def item_is_ready(self, row: int) -> bool:
        try:
            node_number = self.item(row).data()
        except AttributeError:
            return False
        traj = self.get_trajectory(node_number)
        if isinstance(traj, Trajectory):
            return True
        return False

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        try:
            node_number = self.item(row).data()
        except AttributeError:
            return False
        retcode = super().removeRow(row, parent)
        instance = self._trajectory_instances.pop(node_number)
        filename = self._trajectory_paths.pop(node_number)
        if instance:
            instance.close()
        self.free_name.emit(str(filename))
        self._node_numbers.pop(self._node_numbers.index(node_number))
        thread: LoaderThread = self._loading_threads.pop(node_number)
        try:
            thread.quit()
            thread.terminate()
            timer = QDeadlineTimer(300, Qt.TimerType.CoarseTimer)
            thread.wait(deadline=timer)
        except Exception as e:
            LOG.error("While removing a loader thread, an exception occured: %s", e)
        return retcode
