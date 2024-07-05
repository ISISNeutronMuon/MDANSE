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
from qtpy.QtCore import QAbstractItemModel
from qtpy.QtCore import Slot, Signal, QModelIndex, Qt
from qtpy.QtWidgets import QMenu, QTableView, QAbstractItemView, QMessageBox
from qtpy.QtGui import QStandardItem, QContextMenuEvent

from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Visualisers.JobLogInfo import JobLogInfo


class RunTable(QTableView):
    item_details = Signal(object)
    jobs_logs = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)
        vh = self.verticalHeader()
        vh.setVisible(False)

    def setModel(self, model: QAbstractItemModel) -> None:
        result = super().setModel(model)
        self.model().dataChanged.connect(self.resizeColumnsToContents)
        return result

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if index.row() == -1:
            # block right click when it's not on a job
            return
        model = self.model()
        item = model.itemData(index)
        menu = QMenu()
        self.populateMenu(menu, item)
        menu.exec_(event.globalPos())

    def populateMenu(self, menu: QMenu, item: QStandardItem):
        entry, _, _, _ = self.getJobObjects()
        job_state = entry._current_state
        for action, method in [
            ("Delete", self.deleteNode),
            ("Pause", self.pauseJob),
            ("Resume", self.unpauseJob),
            ("Terminate", self.terminateJob),
            # ("Kill", self.killJob),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            if action not in job_state._allowed_actions:
                temp_action.setEnabled(False)

    def getJobObjects(self):
        model = self.model()
        index = self.currentIndex()
        item_row = index.row()
        entry_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        try:
            entry_number = int(entry_number)
        except ValueError:
            LOG.error(f"Could not use {entry_number} as int")
            return
        job_entry, job_watcher_thread, job_process, log_listener = (
            model.existing_jobs[entry_number],
            model.existing_threads[entry_number],
            model.existing_processes[entry_number],
            model.existing_listeners[entry_number],
        )
        return job_entry, job_watcher_thread, job_process, log_listener

    @Slot()
    def deleteNode(self):
        entry, watcher, process, listener = self.getJobObjects()
        try:
            process.close()
            listener.stop()
        except ValueError:
            LOG.error("The process is still running!")
        else:
            model = self.model()
            index = self.currentIndex()
            model.removeRow(index.row())
            if model.rowCount() == 0:
                for i in reversed(range(model.columnCount())):
                    model.removeColumn(i)
            self.item_details.emit("")

    @Slot()
    def pauseJob(self):
        entry, _, _, _ = self.getJobObjects()
        entry.pause_job()

    @Slot()
    def unpauseJob(self):
        entry, _, _, _ = self.getJobObjects()
        entry.unpause_job()

    @Slot()
    def killJob(self):
        entry, _, process, listener = self.getJobObjects()
        process.kill()
        entry.kill_job()
        listener.stop()

    @Slot()
    def terminateJob(self):
        confirmation_box = QMessageBox(
            QMessageBox.Icon.Question,
            "You are about to terminate a job",
            "All progress will be lost if you terminate your job. Do you really want to teminate?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self,
        )
        result = confirmation_box.exec()
        LOG.info(f"QMessageBox result = {result}")
        if result == QMessageBox.StandardButton.Yes.value:
            entry, _, process, listener = self.getJobObjects()
            process.terminate()
            entry.terminate_job()
            listener.stop()

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        index = self.currentIndex()
        item_row = index.row()
        node_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        job_entry = model.existing_jobs[node_number]
        self.item_details.emit(job_entry.text_summary())
        self.jobs_logs.emit(job_entry.msgs)

    def connect_to_visualiser(self, visualiser: TextInfo) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : TextInfo
            A visualiser to connect to this view.
        """
        if type(visualiser) is TextInfo:
            self.item_details.connect(visualiser.update_panel)
        elif type(visualiser) is JobLogInfo:
            self.jobs_logs.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser "
                f"{type(visualiser)}"
            )
