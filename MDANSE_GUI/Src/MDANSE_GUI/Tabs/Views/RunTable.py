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
from qtpy.QtCore import Slot, Signal, QModelIndex
from qtpy.QtWidgets import QMenu, QTableView, QAbstractItemView
from qtpy.QtGui import QStandardItem, QContextMenuEvent

from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo


class RunTable(QTableView):
    item_details = Signal(object)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)

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
        for action, method in [("Delete", self.deleteNode)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        model.removeRow(index.row())
        if model.rowCount() == 0:
            for i in reversed(range(model.columnCount())):
                model.removeColumn(i)
        self.item_details.emit("")

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data()
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
