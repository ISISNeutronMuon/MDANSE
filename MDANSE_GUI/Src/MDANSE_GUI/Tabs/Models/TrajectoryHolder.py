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

from MDANSE_GUI.Tabs.Models import GeneralModel
from MDANSE_GUI.MolecularViewer.Contents import TrajectoryState


class TrajectoryHolder(GeneralModel):

    trajectory_state = Signal(object)

    def __init__(self, *args, **kwargs):
        super().init(*args, **kwargs)
        self._extra_nodes = {}

    @Slot(tuple)
    def append_object(self, input: tuple):
        thing, label = input
        retval = super().append_object(tuple)
        self._extra_nodes[retval] = TrajectoryState(thing)
        return retval

    def removeRow(self, row: int, parent: QModelIndex = None):
        node_number = super().removeRow(row, parent)
        self._extra_nodes.pop(node_number)
