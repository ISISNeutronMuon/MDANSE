# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/RegistryViewer.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from PyQt6.QtCore import QAbstractItemModel, QObject
from qtpy.QtCore import Slot, Signal, QModelIndex, Qt
from qtpy.QtWidgets import (
    QApplication,
    QMenu,
    QTableView,
    QAbstractItemView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionProgressBar,
    QProgressBar,
)
from qtpy.QtGui import QStandardItem, QContextMenuEvent

from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo


class JobProgress(QStyledItemDelegate):
    """This is a delegate widget which is meant to
    draw a progress bar in the second column of the Run Table.
    """

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.progress_option = QStyleOptionProgressBar()
        self.progress_option.minimum = 0
        self.progress_option.maximum = 100
        self.progress_option.textVisible = True

    def paint(self, painter, option, index):
        text = index.data(role=Qt.ItemDataRole.DisplayRole)
        try:
            progress = int(index.data(role=Qt.ItemDataRole.UserRole))
        except TypeError:
            progress = None
        if text is None:
            super().paint(painter, option, index)
            return
        if "percent" in text and progress is not None:
            rectangle = option.rect
            self.progress_option.rect = rectangle
            self.progress_option.progress = progress
            self.progress_option.text = text
            QApplication.style().drawControl(
                QStyle.CE_ProgressBar, self.progress_option, painter
            )
            return
        super().paint(painter, option, index)


class RunTable(QTableView):
    item_details = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)
        # delegate = JobProgress(self)
        # self.setItemDelegate(delegate)
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
        entry, _, _ = self.getJobObjects()
        job_state = entry._current_state
        for action, method in [
            ("Delete", self.deleteNode),
            ("Pause", self.pauseJob),
            ("Resume", self.unpauseJob),
            ("Terminate", self.terminateJob),
            ("Kill", self.killJob),
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
            print(f"Could not use {entry_number} as int")
            return
        job_entry, job_watcher_thread, job_process = (
            model.existing_jobs[entry_number],
            model.existing_threads[entry_number],
            model.existing_processes[entry_number],
        )
        return job_entry, job_watcher_thread, job_process

    @Slot()
    def deleteNode(self):
        entry, watcher, process = self.getJobObjects()
        try:
            process.close()
        except ValueError:
            print("The process is still running!")
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
        entry, _, _ = self.getJobObjects()
        entry.pause_job()

    @Slot()
    def unpauseJob(self):
        entry, _, _ = self.getJobObjects()
        entry.unpause_job()

    @Slot()
    def killJob(self):
        entry, _, process = self.getJobObjects()
        process.kill()
        entry.kill_job()

    @Slot()
    def terminateJob(self):
        entry, _, process = self.getJobObjects()
        process.terminate()
        entry.terminate_job()

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        index = self.currentIndex()
        item_row = index.row()
        node_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        job_entry = model.existing_jobs[node_number]
        self.item_details.emit(job_entry.text_summary())

    def connect_to_visualiser(self, visualiser: TextInfo) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : TextInfo
            A visualiser to connect to this view.
        """
        if isinstance(visualiser, TextInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser "
                f"{type(visualiser)}"
            )
