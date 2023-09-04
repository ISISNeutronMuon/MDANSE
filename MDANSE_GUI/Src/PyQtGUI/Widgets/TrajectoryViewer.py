# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Widgets/Generator.py
# @brief     Here we can generate some Widgets
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

import typing

from icecream import ic
from qtpy.QtWidgets import QTreeView, QWidget, QMenu
from qtpy.QtCore import Signal, Slot, QModelIndex
from qtpy.QtGui import QContextMenuEvent

from MDANSE_GUI.PyQtGUI.DataViewModel.TrajectoryHolder import DataTreeItem


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
        ic("Emitting items ancestor. Item:", item)
        anc = item.ancestors()
        ic("ancestor:", anc[-1])
        self.pickedAncestor.emit(anc[-1])
        
    # def contextMenuEvent(self, event: QContextMenuEvent) -> None:
    #     index = self.indexAt(event.pos())
    #     model = self.model()
    #     item = model.itemData()
    #     # item = index.data()
    #     ic(index)
    #     ic(item)
    #     menu = QMenu()
    #     self.populateMenu(menu)
    #     picked = menu.exec(menu.)
    #     res = menu.exec_(event.globalPos())


    #     return super().contextMenuEvent(event)

    def populateMenu(menu: QMenu, item: DataTreeItem):
        for action in item.possibleActions():
            menu.addAction(action)