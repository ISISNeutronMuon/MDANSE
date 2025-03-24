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
from MDANSE.MLogging import LOG
from qtpy.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QStandardItem
from qtpy.QtWidgets import QAbstractItemView, QMenu, QMessageBox, QTableView

from MDANSE_GUI.Tabs.Views.Delegates import ProgressDelegate
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D


class SelectionTable(QTableView):
    """An MDANSE View for finding atom selections."""

    item_details = Signal(object)
    jobs_logs = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)
        self._progbar = ProgressDelegate()
        self.setItemDelegateForColumn(1, self._progbar)
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
        _ = self.getSelection()
        for action, method in [
            ("Delete", self.deleteNode),
        ]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

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
        return

    @Slot()
    def deleteNode(self):
        entry, watcher, process, listener = self.getJobObjects()
        try:
            process.close()
        except ValueError:
            LOG.error("The process is still running!")
        else:
            model = self.model()
            index = self.currentIndex()
            model.removeRow(index.row())
            self.item_details.emit("")
            self.jobs_logs.emit(([], []))

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        index = self.currentIndex()
        item_row = index.row()
        node_number = model.index(item_row, 0).data(role=Qt.ItemDataRole.UserRole)
        job_entry = model.existing_jobs[node_number]
        self.item_details.emit(job_entry.text_summary())
        self.jobs_logs.emit(job_entry.handler.msgs_and_levels())

    def connect_to_visualiser(self, visualiser: TextInfo) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : TextInfo
            A visualiser to connect to this view.

        """
        if type(visualiser) is TextInfo:
            self.item_details.connect(visualiser.update_panel)
        if type(visualiser) is View3D:
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}"
            )
