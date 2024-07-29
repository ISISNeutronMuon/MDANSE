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

from qtpy.QtCore import Slot, Signal, QModelIndex
from qtpy.QtWidgets import QListView, QAbstractItemView

from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import (
    InstrumentDetails,
    SimpleInstrument,
)


class InstrumentList(QListView):
    item_details = Signal(object)
    item_name = Signal(str)
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.clicked.connect(self.item_picked)

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
        instrument = model._nodes[node_number]
        self.item_details.emit(instrument)

    def add_instrument(self):
        model = self.model()
        new_instrument = SimpleInstrument()
        model.append_object((new_instrument, "New Instrument"))

    def connect_to_visualiser(self, visualiser: InstrumentDetails) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : View3D or TrajectoryInfo
            A visualiser to connect to this view.
        """
        try:
            self.item_details.connect(visualiser.update_panel)
        except Exception as e:
            LOG.error(f"Failed to connect InstrumentList to visualiser: {e}")
