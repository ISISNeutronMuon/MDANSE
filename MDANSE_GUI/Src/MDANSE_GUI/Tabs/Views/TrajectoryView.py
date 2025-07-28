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

from qtpy.QtCore import QModelIndex, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QStandardItem
from qtpy.QtWidgets import QAbstractItemView, QListView, QMenu

from MDANSE_GUI.Tabs.Visualisers.TrajectoryInfo import TrajectoryInfo
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D


class TrajectoryView(QListView):
    item_details = Signal(tuple)
    item_name = Signal(str)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if index.row() == -1:
            # block right click when it's not on a trajectory
            return
        model = self.model()
        if not model.item_is_ready(index.row()):
            return
        item = model.itemData(index)
        menu = QMenu()
        self.populateMenu(menu, item)
        menu.exec_(event.globalPos())

    def populateMenu(self, menu: QMenu, item: QStandardItem):
        for action, method in [("Delete", self.deleteNode)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        model.removeRow(index.row())
        self.item_details.emit(("", None))

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data()
        trajectory = model.get_trajectory(node_number)
        if trajectory is None:
            self.item_details.emit(("", None))
        elif isinstance(trajectory, str):
            self.item_details.emit((trajectory, None))
        else:
            self.item_details.emit((trajectory._filename, trajectory))

    def connect_to_visualiser(self, visualiser: View3D | TrajectoryInfo) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : View3D or TrajectoryInfo
            A visualiser to connect to this view.
        """
        if isinstance(visualiser, View3D) or isinstance(visualiser, TrajectoryInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}"
            )
