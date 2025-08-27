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

from qtpy.QtCore import QMimeData, QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QDrag, QMouseEvent
from qtpy.QtWidgets import QAbstractItemView, QApplication, QTreeView

from MDANSE.MLogging import LOG
from MDANSE_GUI.DataViewModel.ActionsHolder import ActionsHolder
from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeItem
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
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.click_position = None

        self.clicked.connect(self.on_select_action)
        self.clicked.connect(self.item_picked)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self.click_position = e.position()
        if self.model() is None:
            return None
        return super().mousePressEvent(e)

    def on_select_action(self, index):
        model = self.model()
        item = model.itemFromIndex(index)
        text = item.text()
        LOG.info(f"tree: clicked on {text}")
        self.jobname_selected.emit(text)

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        node_number = model.itemFromIndex(index).data(Qt.ItemDataRole.UserRole)
        try:
            job_description = model._docstrings[node_number]
        except KeyError:
            job_description = "No further information"
        self.item_details.emit(job_description)  # this should emit the job name

    def connect_to_visualiser(self, visualiser: Action | TextInfo) -> None:
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
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}"
            )
