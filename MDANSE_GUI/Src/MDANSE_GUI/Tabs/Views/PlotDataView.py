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
from qtpy.QtGui import QContextMenuEvent, QDrag, QMouseEvent, QStandardItem
from qtpy.QtWidgets import QAbstractItemView, QApplication, QMenu, QTreeView

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlotDataModel import BasicPlotDataItem, MDADataStructure
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset
from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter
from MDANSE_GUI.Tabs.Visualisers.PlotDataInfo import PlotDataInfo
from MDANSE_GUI.Widgets.DataDialog import DataDialog


class PlotDataView(QTreeView):
    """Viewer of the MDA file contents.

    It is used for selecting data from different MDA files that
    will be plotted together.
    """

    dataset_selected = Signal(object)
    execute_action = Signal(object)
    item_details = Signal(object)
    error = Signal(str)
    fast_plotting_data = Signal(object)
    free_name = Signal(str)
    fast_plotting_data = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.click_position = None
        self.clicked.connect(self.on_select_dataset)
        # self.data_dialog = DataDialog(self)
        self._data_packet = None

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:
        self.click_position = e.position()
        if self.model() is None:
            return None
        index = self.indexAt(e.pos())
        model = self.model()
        inner_node = model.inner_object(index)
        if isinstance(inner_node, MDADataStructure):
            data_nodes = model.itemFromIndex(index).recursive_children(
                recursion_limit=-1
            )
            file_node = model.parent_object(index)
            self.quick_plot_data(data_nodes, file_node, main_only=True)
        else:
            if (current_item := model.itemFromIndex(index)) is None:
                return
            data_nodes = current_item.recursive_children(recursion_limit=1)
            file_node = model.parent_object(index)
            self.quick_plot_data(data_nodes, file_node)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        self.click_position = e.position()
        if self.model() is None:
            return None
        return super().mousePressEvent(e)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if index.row() == -1:
            # block right click when it's not on a trajectory
            return
        if index.parent().data() is not None:
            return
        model = self.model()
        qitem = model.itemFromIndex(index)
        if qitem.parent() is not None:
            model = self.model()
            item = model.itemFromIndex(index)
            text = item.text()
            mda_data_structure = model.inner_object(index)
            try:
                packet = text, mda_data_structure._file
            except AttributeError:
                packet = text, mda_data_structure.file
            self._data_packet = packet
        menu = QMenu()
        self.populateMenu(menu, index)
        menu.exec_(event.globalPos())

    def populateMenu(self, menu: QMenu, index: QModelIndex):
        for action, method in [("Delete", self.deleteNode)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    @Slot()
    def deleteNode(self):
        model = self.model()
        index = self.currentIndex()
        mda_data_structure = model.parent_object(index)
        try:
            filename = mda_data_structure._file.filename
        except AttributeError:
            filename = mda_data_structure.file
        self.free_name.emit(str(filename))
        parent_node = self.currentIndex()
        while parent_node.column() > 1:
            parent_node = parent_node.parent()
        model.removeRow(parent_node.row())
        self.item_details.emit("")

    def on_select_dataset(self, index):
        model = self.model()
        item = model.itemFromIndex(index)
        text = item.child_path
        mda_data_structure = model.inner_object(index)
        try:
            packet = text, mda_data_structure._file
        except AttributeError:
            packet = text, mda_data_structure.file
        self.dataset_selected.emit(packet)
        if hasattr(mda_data_structure, "_metadata"):
            self.item_details.emit(mda_data_structure._metadata)
        else:
            try:
                text += "\n"
                for attr in mda_data_structure.attrs:
                    text += f"{attr}: {mda_data_structure.attrs[attr]}\n"
                self.item_details.emit(text)
            except Exception:
                self.item_details.emit("No additional information included.")

    def quick_plot_data(
        self,
        data_nodes: list[BasicPlotDataItem],
        mda_data_structure: MDADataStructure,
        *,
        main_only: bool = False,
    ):
        """Plot several datasets in a new plot instance.

        Parameters
        ----------
        data_nodes : list[BasicPlotDataItem]
            Data model items collected for plotting.
        mda_data_structure : MDADataStructure
            The common HDF5 file from which the datasets originate.
        main_only: bool
            if True, only plot datasets with the 'main' tag

        """
        model = PlottingContext()
        file = mda_data_structure._file
        for data_node in data_nodes:
            if not data_node.child_path:
                continue
            if main_only:
                try:
                    tags = file[data_node.child_path].attrs["tags"]
                except KeyError:
                    continue
                if "main" not in tags:
                    continue
                dataset = SingleDataset(
                    data_node.child_path,
                    file,
                    linestyle="--" if "partial" in tags else "-",
                )
            else:
                dataset = SingleDataset(data_node.child_path, file)
            model.add_dataset(dataset)
        self.fast_plotting_data.emit(model)

    @Slot(QModelIndex)
    def item_picked(self, index: QModelIndex):
        """Respond to an item receiving a click in the view.

        Here it will send the dataset to the DataPlotter model.

        Parameters
        ----------
        index : QModelIndex
            _description_

        """
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
        self,
        visualiser: DataPlotter | PlotDataInfo,
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
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}",
            )
