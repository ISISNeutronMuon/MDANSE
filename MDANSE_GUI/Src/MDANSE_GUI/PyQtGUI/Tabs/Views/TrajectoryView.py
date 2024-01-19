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

import os

from qtpy.QtCore import QObject, Slot, Signal, QModelIndex
from qtpy.QtWidgets import QMenu, QListView
from qtpy.QtGui import QStandardItem, QContextMenuEvent


class TrajectoryView(QListView):
    item_details = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked.connect(self.item_picked)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        model = self.model()
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
        self.item_details.emit("")

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data()
        trajectory = model._nodes[node_number]
        self.item_details.emit(trajectory.info())
