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

from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter
from MDANSE_GUI.Tabs.Visualisers.PlotDataInfo import PlotDataInfo
from MDANSE_GUI.Tabs.Models.PlotDataModel import BasicPlotDataItem


class PlotDataView(QTreeView):
    dataset_selected = Signal(object)
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
        self.clicked.connect(self.on_select_dataset)

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

    def on_select_dataset(self, index):
        model = self.model()
        item = model.itemFromIndex(index)
        text = item.text()
        mda_data_structure = model.inner_object(index)
        try:
            packet = text, mda_data_structure._file
        except AttributeError:
            packet = text, mda_data_structure.file
        self.dataset_selected.emit(packet)

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        model = self.model()
        model_item = model.itemFromIndex(index)
        item_type = model_item._item_type
        mda_data = model.inner_object(index)
        if item_type == "file":
            try:
                description = mda_data._metadata
            except AttributeError:
                description = f"File {mda_data._file.filename}, no further information"
        elif item_type == "dataset":
            dataset = model.inner_object(index)
            description = f"{dataset}{model_item.data(role=Qt.ItemDataRole.UserRole)}\n"
            for key in dataset.attrs.keys():
                description += f"{key}: {dataset.attrs[key]}\n"
        elif item_type == "group":
            dataset = model.inner_object(index)
            description = f"{dataset}{model_item.data(role=Qt.ItemDataRole.UserRole)}\n"
            for key in dataset.attrs.keys():
                description += f"{key}: {dataset.attrs[key]}\n"
        else:
            description = "generic item"
        self.item_details.emit(description)  # this should emit the job name

    def connect_to_visualiser(
        self, visualiser: Union[DataPlotter, PlotDataInfo]
    ) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.
        """
        if isinstance(visualiser, DataPlotter):
            self.dataset_selected.connect(visualiser.accept_data)
        elif isinstance(visualiser, PlotDataInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser "
                f"{type(visualiser)}"
            )
