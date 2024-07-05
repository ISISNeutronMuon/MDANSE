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
import logging
import typing

from qtpy.QtWidgets import QTreeView, QWidget, QMenu
from qtpy.QtCore import Signal, Slot, QModelIndex
from qtpy.QtGui import QContextMenuEvent

from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeItem


LOG = logging.getLogger("MDANSE")


class TrajectoryViewer(QTreeView):
    """A modified QTreeView which enables context menus to pop
    up for different elements of the workflow.
    """

    itemPicked = Signal(DataTreeItem)
    pickedAncestor = Signal(str)

    def __init__(self, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.clicked.connect(self.requestChildren)

    def requestChildren(self, index: QModelIndex):
        # item = index.data()
        item = self.model().itemFromIndex(index)
        LOG.info(f"Emitting items ancestor. Item: {item}")
        anc = item.ancestors()
        LOG.info(f"ancestor: {anc[-1]}")
        # self.pickedAncestor.emit(anc[-1])
        self.itemPicked.emit(item)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        model = self.model()
        item = model.itemData(index)
        # item = index.data()
        LOG.info(index)
        LOG.info(item)
        menu = QMenu()
        self.populateMenu(menu, item)
        # picked = menu.exec(menu.)
        menu.exec_(event.globalPos())
        # return super().contextMenuEvent(event)

    def populateMenu(self, menu: QMenu, item: DataTreeItem):
        for action, method in [("Delete", self.deleteNode)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        model.removeRow(index.row())
