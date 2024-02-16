# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/Views/ActionsTree.py
# @brief     Here we can generate some Widgets
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************
from icecream import ic
from qtpy.QtWidgets import QTreeView, QAbstractItemView, QApplication
from qtpy.QtCore import Signal, Slot, QModelIndex, Qt, QMimeData
from qtpy.QtGui import QMouseEvent, QDrag

from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeItem
from MDANSE_GUI.DataViewModel.ActionsHolder import ActionsHolder


class ActionsTree(QTreeView):
    jobname_selected = Signal(str)
    execute_action = Signal(object)
    item_details = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.click_position = None

        self.clicked.connect(self.on_select_action)
        self.doubleClicked.connect(self.pop_action_dialog)
        self.clicked.connect(self.item_picked)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self.click_position = e.position()
        if self.model() is None:
            return None
        return super().mousePressEvent(e)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # print("Mouse Move Event!", event.button(), QtCore.Qt.MouseButton.LeftButton)
        if event.buttons() == Qt.MouseButton.LeftButton:
            # if event.button():
            print("dragging")
            new_position = event.position()
            distance = (self.click_position - new_position).manhattanLength()
            if distance > QApplication.startDragDistance():
                drag = QDrag(self)
                mime_data = QMimeData()
                text = self.model().data(
                    self.currentIndex(), Qt.ItemDataRole.DisplayRole
                )
                mime_data.setText(text)
                drag.setMimeData(mime_data)
                drag.exec()

    def on_select_action(self, index):
        model = self.model()
        item = model.itemFromIndex(index)
        text = item.text()
        print("tree: clicked on ", text)
        self.jobname_selected.emit(text)

    def pop_action_dialog(self, index):
        model = self.model()
        item = model.itemFromIndex(index)
        # debug
        text = item.text()
        ic(f"About to execute action {text}")
        #
        number = item.data(Qt.ItemDataRole.UserRole)
        ic(f"Node number is {number}")
        if number is None:
            return
        action = model._values[number]
        self.execute_action.emit(action)

    @Slot(DataTreeItem)
    def showValidActions(self, item: DataTreeItem):
        ic("Creating model from", item)
        new_model = ActionsHolder(item)
        self.setModel(new_model)

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data(Qt.ItemDataRole.UserRole)
        try:
            job_description = model._docstrings[node_number]
        except KeyError:
            job_description = "No further information"
        self.item_details.emit(job_description)  # this should emit the job name
