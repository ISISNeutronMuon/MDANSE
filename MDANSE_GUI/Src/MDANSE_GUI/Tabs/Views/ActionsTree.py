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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Research Software Group at ISIS (see AUTHORS)
from typing import Union

from icecream import ic
from qtpy.QtWidgets import QTreeView, QAbstractItemView, QApplication
from qtpy.QtCore import Signal, Slot, QModelIndex, Qt, QMimeData
from qtpy.QtGui import QMouseEvent, QDrag

from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeItem
from MDANSE_GUI.DataViewModel.ActionsHolder import ActionsHolder
from MDANSE_GUI.Tabs.Visualisers.Action import Action
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo


class ActionsTree(QTreeView):
    jobname_selected = Signal(str)
    execute_action = Signal(object)
    item_details = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHeaderHidden(True)
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

    def connect_to_visualiser(self, visualiser: Union[Action, TextInfo]) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.
        """
        if isinstance(visualiser, Action):
            self.jobname_selected.connect(visualiser.update_panel)
        elif isinstance(visualiser, TextInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser "
                f"{type(visualiser)}"
            )
