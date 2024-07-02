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
from typing import Union

from icecream import ic
from qtpy.QtWidgets import QTreeView, QAbstractItemView, QApplication
from qtpy.QtCore import Signal, Slot, QModelIndex, Qt, QMimeData
from qtpy.QtGui import QMouseEvent, QDrag


class PlotDetailsView(QTreeView):
    details_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def connect_to_visualiser(self, visualiser) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.
        """
        self.details_changed.connect(visualiser.update_plot_details)
