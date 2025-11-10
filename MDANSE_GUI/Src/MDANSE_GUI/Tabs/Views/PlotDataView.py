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

import html

import h5py
import numpy as np
import numpy.typing as npt
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QMouseEvent
from qtpy.QtWidgets import QAbstractItemView, QMenu, QTreeView

from MDANSE.Framework.Configurators.QVectorsConfigurator import QVectorsConfigurator
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlotDataModel import BasicPlotDataItem, MDADataStructure
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset
from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo

BIN_STEP_PADDING = 2.0


def shell_to_modq(shell_index: int, parent: h5py.Dataset) -> npt.NDArray[float]:
    """Finds the vector shell dataset and returns arrays of q vector lengths.

    Parameters
    ----------
    shell_index : int
        Index of the MDANSE q vector shell in the HDF5 data structure.
    parent : h5py.Dataset
        HDF5 object holding the shell_N keys, where N is shell_index.

    Returns
    -------
    npt.NDArray[float]
        A 1D array of q-vector lengths.
    """
    qvectors = parent[f"shell_{shell_index}/qvector_array"][:]
    return np.linalg.norm(qvectors, axis=0)


def convert_vectors_to_datasets(
    source: h5py.File | QVectorsConfigurator, main_dstet: str = "vector_generator"
) -> tuple[SingleDataset, SingleDataset]:
    """Create plottable SingleDataset instances showing |q| of generated vectors.

    Parameters
    ----------
    file : h5py.File
        HDF5 file object, typically an .mda file.
    main_dstet : str, optional
        Name of the group with q vector shells, by default "vector_generator".

    Returns
    -------
    Iterable[SingleDataset]
        1D array of vector count vs. |q|, 2D histogram of q vector counts per shell.
    """
    if isinstance(source, h5py.File):
        filename = source.filename
        parent_dset = source[main_dstet]
        qvals = parent_dset["q"][:]
        nshells = len(qvals)
        modq_per_shell = [shell_to_modq(n, parent_dset) for n in range(nshells)]
        if not all(
            "custom_field" in parent_dset[f"shell_{shell_index}/qvector_array"].attrs
            for shell_index in range(nshells)
        ):
            available_vectors = np.array([len(qvecs) for qvecs in modq_per_shell])
        else:
            available_vectors = np.array(
                [
                    [
                        int(x)
                        for x in parent_dset[
                            f"shell_{shell_index}/qvector_array"
                        ].attrs["custom_field"]
                    ]
                    for shell_index in range(nshells)
                ]
            )
    elif isinstance(source, QVectorsConfigurator):
        filename = None
        qvals = np.array(source["shells"])
        nshells = len(qvals)
        modq_per_shell = [
            np.linalg.norm(source["q_vectors"][qvals[n]]["q_vectors"], axis=0)
            for n in range(nshells)
        ]
        available_vectors = np.array(
            [source["q_vectors"][qvals[n]]["n_q_vectors"] for n in range(nshells)]
        )
    mean_q = np.array([np.mean(qvecs) for qvecs in modq_per_shell])
    mean_q_yerr = np.array([np.std(qvecs) for qvecs in modq_per_shell])
    qmin, qmax = np.min(modq_per_shell[0]), np.max(modq_per_shell[nshells - 1])
    q_step = np.mean(np.abs(np.diff(qvals))) if len(qvals) > 1 else 0.1
    bin_step = 0.4 * np.min([np.std(one_shell) for one_shell in modq_per_shell])
    bin_step = 0.2 * q_step if abs(bin_step) < 1e-09 else max(bin_step, 0.05 * q_step)
    common_bins = np.arange(max(0.0, qmin), qmax + 1.1 * bin_step, bin_step)
    qmod_histograms = [np.histogram(qmods, common_bins)[0] for qmods in modq_per_shell]
    stacked_histograms = np.vstack(qmod_histograms)
    xvals = common_bins[1:] - np.diff(common_bins) / 2
    nvec_per_q = SingleDataset(
        "Available vectors",
        None,
        linestyle=":",
        marker="o",
        data=available_vectors,
        plot_axes={"|q|": qvals},
        axes_units={"|q|": "1/nm"},
        optional_filename=filename,
    )
    real_q_ideal_q = SingleDataset(
        "Mean |q|",
        None,
        linestyle="-",
        marker=".",
        data=mean_q,
        plot_axes={"|q|": qvals},
        axes_units={"|q|": "1/nm"},
        data_unit="1/nm",
        yerror=mean_q_yerr,
        optional_filename=filename,
    )
    vecs_per_qbin = SingleDataset(
        "Shell population",
        None,
        data=stacked_histograms,
        data_unit="counts",
        plot_axes={"|q|": qvals, "q_bin": xvals},
        axes_units={"|q|": "1/nm", "q_bin": "1/nm"},
        optional_filename=filename,
    )
    return nvec_per_q, real_q_ideal_q, vecs_per_qbin


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
    fast_plotting_vectors = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHeaderHidden(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.click_position = None
        self.clicked.connect(self.on_select_dataset)
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
        for action, method in [("Vector summary", self.plot_vectors)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            temp_action.setEnabled(self.model().itemFromIndex(index).has_vectors)
        menu.addSeparator()
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
            self.item_details.emit(
                html.escape(
                    "\n".join(
                        f"{key}: {item}"
                        for key, item in mda_data_structure._metadata.items()
                    )
                )
            )
        else:
            try:
                text += "\n"
                for attr in mda_data_structure.attrs:
                    text += f"{attr}: {mda_data_structure.attrs[attr]}\n"
                self.item_details.emit(html.escape(text))
            except Exception:
                self.item_details.emit("No additional information included.")

    def plot_vectors(
        self,
    ):
        source_model = self.model()
        index = self.currentIndex()
        mda_data_structure = source_model.parent_object(index)
        file = mda_data_structure._file
        LOG.debug("Running plot_vectors on file %s", file.filename)
        model = PlottingContext()
        for qvec_dataset in convert_vectors_to_datasets(file):
            model.add_dataset(qvec_dataset)
        self.fast_plotting_vectors.emit(model)

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
        elif item_type in {"dataset", "group"}:
            dataset = model.inner_object(index)
            description = f"{dataset}{model_item.data(role=Qt.ItemDataRole.UserRole)}\n"
            for key in dataset.attrs:
                description += f"{key}: {dataset.attrs[key]}\n"
        else:
            description = "generic item"
        self.item_details.emit(
            html.escape(description)
        )  # this should emit the job name

    def connect_to_visualiser(
        self,
        visualiser: DataPlotter | TextInfo,
    ) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.

        """
        if isinstance(visualiser, DataPlotter):
            self.dataset_selected.connect(visualiser.accept_data)
        elif isinstance(visualiser, TextInfo):
            self.item_details.connect(visualiser.update_panel)
        else:
            raise NotImplementedError(
                f"Unable to connect view {type(self)} to visualiser {type(visualiser)}",
            )
