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

from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractItemView, QMenu, QMessageBox, QTableView

from MDANSE.Framework.Jobs.JobStatus import ALLOWED_ACTIONS
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.JobHolder import Job, JobHolder
from MDANSE_GUI.Tabs.Views.Delegates import ProgressDelegate
from MDANSE_GUI.Tabs.Visualisers.JobLogInfo import JobLogInfo
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo

PROGBAR_COLUMN = 1


class RunTable(QTableView):
    item_details = Signal(object)
    jobs_logs = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)
        self._progbar = ProgressDelegate()
        self.setItemDelegateForColumn(PROGBAR_COLUMN, self._progbar)
        vh = self.verticalHeader()
        vh.setVisible(False)

    def setModel(self, model: QStandardItemModel) -> None:
        result = super().setModel(model)
        model.itemChanged.connect(self.selective_resize)
        model.new_job_started.connect(self.name_column_resize)
        return result

    @Slot()
    def name_column_resize(self):
        self.resizeColumnToContents(0)

    @Slot("QStandardItem*")
    def selective_resize(self, item: QStandardItem):
        if (colind := item.column()) == PROGBAR_COLUMN:
            return
        self.resizeColumnToContents(colind)

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

    def populateMenu(self, menu: QMenu, item: QStandardItem) -> None:
        job = self.getJobObjects()
        job_state = job.entry.job.state
        for action, method in [
            ("Delete", self.deleteNode),
            ("Pause", self.pauseJob),
            ("Resume", self.unpauseJob),
            ("Terminate", self.terminateJob),
            # ("Kill", self.killJob),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            temp_action.setEnabled(action in ALLOWED_ACTIONS[job_state])

    def getJobObjects(self) -> Job | None:
        model: JobHolder = self.model()
        index = self.currentIndex()
        item_row = index.row()
        entry_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        try:
            entry_number = int(entry_number)
        except ValueError:
            LOG.error(f"Could not use {entry_number} as int")
            return None

        return model.jobs[entry_number]

    @Slot()
    def deleteNode(self) -> None:
        job = self.getJobObjects()
        try:
            job.process.close()
        except ValueError:
            LOG.error("The process is still running!")
        else:
            model = self.model()
            index = self.currentIndex()
            model.removeRow(index.row())
            self.item_details.emit("")
            self.jobs_logs.emit(([], []))

    @Slot()
    def pauseJob(self) -> None:
        job = self.getJobObjects()
        job.entry.pause_job()

    @Slot()
    def unpauseJob(self) -> None:
        job = self.getJobObjects()
        job.entry.unpause_job()

    @Slot()
    def killJob(self) -> None:
        job = self.getJobObjects()
        job.process.kill()
        job.entry.kill_job()
        job.listener.stop()

    @Slot()
    def terminateJob(self) -> None:
        confirmation_box = QMessageBox(
            QMessageBox.Icon.Question,
            "You are about to terminate a job",
            "All progress will be lost if you terminate your job. Do you really want to teminate?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self,
        )
        result = confirmation_box.exec()
        LOG.info(f"QMessageBox result = {result}")
        if result == QMessageBox.StandardButton.Yes:
            job = self.getJobObjects()
            # process is not alive, the job probably finished already
            if job.process.is_alive():
                job.process.terminate()
                job.process.join()
                job.entry.terminate_job()
                job.listener.stop()

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex) -> None:
        model = self.model()
        index = self.currentIndex()
        item_row = index.row()
        node_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        job_entry = model.jobs[node_number].entry
        self.item_details.emit(job_entry.text_summary())
        self.jobs_logs.emit(job_entry.handler.msgs_and_levels())

    def connect_to_visualiser(self, visualiser: TextInfo | JobLogInfo) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : TextInfo | JobLogInfo
            A visualiser to connect to this view.
        """
        if isinstance(visualiser, JobLogInfo):
            self.jobs_logs.connect(visualiser.update_panel)
        elif isinstance(visualiser, TextInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}"
            )
