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
import json
from collections.abc import Generator
from typing import Any

import h5py
import numpy as np
import numpy.typing as npt
from more_itertools import always_iterable
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QPoint, Qt, Signal, Slot
from qtpy.QtGui import QContextMenuEvent, QMouseEvent
from qtpy.QtWidgets import QAbstractItemView, QMenu, QTreeView

from MDANSE.Framework.Configurators.QVectorsConfigurator import QVectorsConfigurator
from MDANSE.Framework.QVectors.IQVectors import WIDTH_NONZERO_LIMIT
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlotDataModel import BasicPlotDataItem, MDADataStructure
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset
from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo

MAX_BINS_PER_SHELL = 20
MIN_BINS_PER_SHELL = 1
MAX_BINS_PER_PLOT = 180

WEIGHTS_MULTIPLIER = 100


def qvector_binning_from_dict(
    qvector_params: dict[str, Any],
    n_segments: int = 10,
) -> npt.NDArray[float] | None:
    """Calculate the range of |q| bins from the vector generator parameters.

    Parameters
    ----------
    qvector_params : dict[str, Any]
        Input parameters of any subclass of IQVectors given as a dictionary.
    n_segments : int, optional
        Starting value of the number of histogram bins per vector shell, by default 10

    Returns
    -------
    npt.NDArray[float] | None
        A 1D array of |q| bin limits.
    """
    if (step_params := qvector_params.get("shells")) is None:
        return None
    start, end, step_size = step_params
    width = qvector_params.get("width")
    return qvector_binning_general(start, end, step_size, width, n_segments)


def qvector_binning_general(
    start: float,
    end: float,
    step_size: float,
    width: float | None,
    n_segments: int,
) -> npt.NDArray[float]:
    """Calculate the |q| bin limits based of vector shell limits and steps.

    Parameters
    ----------
    start : float
        Lower limit of the |q| shell range.
    end : float
        Upper limit of the |q| shell range.
    step_size : float
        Step size of the |q| shell range.
    width : float | None
        Width of a single shell in |q| units (1/nm).
    n_segments : int
        Starting value of number of histogram bins per shell.

    Returns
    -------
    npt.NDArray[float]
        A 1D array of |q| histogram bin limits.
    """
    if end < start:
        start, end = end, start
    if np.isclose(start, end) and (
        width is None or np.isclose(width, 0, atol=WIDTH_NONZERO_LIMIT)
    ):
        return np.array([start - 0.15, start - 0.05, start + 0.05, start + 0.15])

    width = abs(width) if width else width
    step_size = abs(step_size)

    def get_bin_width(n_segments: int) -> tuple[float, float]:
        """Return the bin width based on shell width and shell separation."""
        if np.isclose(start, end):
            return width / n_segments, width
        elif width is None or width <= step_size / 2:
            return step_size / n_segments, step_size
        else:
            return step_size / n_segments, width

    def get_first_last_values(
        bin_width: float, peak_width: float
    ) -> tuple[float, float]:
        """Return the limits of the binning range based on the shell and bin sizes."""
        bins_per_shell = peak_width // bin_width
        if bins_per_shell > MAX_BINS_PER_SHELL or bins_per_shell < MIN_BINS_PER_SHELL:
            bins_per_shell = min(
                max(MIN_BINS_PER_SHELL, bins_per_shell),
                MAX_BINS_PER_SHELL,
            )
            bin_width = peak_width / bins_per_shell
        first_value = start - 0.5 * (bins_per_shell + 1) * bin_width
        last_value = end + 0.5 * (bins_per_shell + 1.01) * bin_width
        return first_value, last_value

    bin_width, peak_width = get_bin_width(n_segments)
    first_value, last_value = get_first_last_values(bin_width, peak_width)
    common_binning = np.arange(
        first_value,
        last_value,
        bin_width,
    )
    last_binning_length = len(common_binning)
    while len(common_binning) > MAX_BINS_PER_PLOT:
        bin_width *= 2
        first_value, last_value = get_first_last_values(bin_width, peak_width)
        common_binning = np.arange(
            first_value,
            last_value,
            bin_width,
        )
        if len(common_binning) == last_binning_length:
            break
        last_binning_length = len(common_binning)
    offset = np.min(np.abs(start - common_binning)) / bin_width
    common_binning -= (offset - 0.5) * bin_width
    return common_binning


def shell_to_modq(shell_index: int, parent: h5py.Dataset) -> npt.NDArray[float]:
    """Find the vector shell dataset and returns arrays of q vector lengths.

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


def vector_angular_datasets(
    source: QVectorsConfigurator,
    shell_key: float,
) -> tuple[SingleDataset, SingleDataset]:
    """Return a specific q-vector shell as spherical coordinate angle datasets.

    Parameters
    ----------
    source : QVectorsConfigurator
        An instance of the QVectorsConfigurator in the GUI.
    shell_key : float
        The |q| of the vector shell.

    Returns
    -------
    tuple[SingleDataset, SingleDataset]
        Datasets of polar and azimuthal angles.
    """
    q_array = source["q_vectors"][shell_key]["q_vectors"]
    q_weights = source["q_vectors"][shell_key]["weights"]
    return angular_datasets_from_qarray(q_array, q_weights)


def angular_datasets_from_qarray(
    q_array: npt.NDArray[float],
    weight_array: npt.NDArray[float],
    filename: str | None = None,
) -> tuple[SingleDataset, SingleDataset]:
    """Convert an array of q vectors into two datasets of spherical angles.

    Parameters
    ----------
    q_array : npt.NDArray[float]
        A (3,N) array of reciprocal space vectors.
    weight_array: npt.NDArray[float],
        Array of weights per vector, based the multiplicity of each vector.
    filename : str | None, optional
        Name of the file to be shown in plot details, by default None

    Returns
    -------
    tuple[SingleDataset, SingleDataset]
        Datasets of polar and azimuthal angles.
    """
    inplane_r = np.linalg.norm(q_array[:2, :], axis=0)
    polar_angles = np.arctan2(inplane_r, q_array[2, :])
    azimuthal_angles = np.arctan2(q_array[1, :], q_array[0, :])
    results = []
    rounding_precision = 3
    for input_angles, label, xlabel, normalise, hist_range in (
        (
            polar_angles,
            r"Polar angle, NORMALISED: counts/sin($\theta$)",
            r"$\theta$",
            True,
            (0, np.pi),
        ),
        (azimuthal_angles, "Azimuthal angle", r"$\phi$", False, (-np.pi, np.pi)),
    ):
        angles = np.round(input_angles, rounding_precision)
        counts, bins = np.histogram(angles, weights=weight_array, range=hist_range)
        unique_counts, _ = np.histogram(angles, bins=bins)
        mean_angles = (bins[1:] + bins[:-1]) / 2
        if normalise:
            counts = counts / np.sin(mean_angles)
        dataset = SingleDataset(
            label,
            None,
            linestyle="-",
            marker="o",
            data=np.vstack((counts, unique_counts)),
            plot_axes={xlabel: mean_angles},
            axes_units={xlabel: "rad"},
            data_unit="rad",
            optional_filename=filename,
        )
        results.append(dataset)
    return results


def vector_projection_datasets(
    source: QVectorsConfigurator,
    shell_key: float,
) -> tuple[SingleDataset, SingleDataset, SingleDataset, SingleDataset]:
    """Return a specific q-vector shell as Cartesian coordinate datasets.

    Parameters
    ----------
    source : QVectorsConfigurator
        An instance of the QVectorsConfigurator in the GUI.
    shell_key : float
        The |q| of the vector shell.

    Returns
    -------
    tuple[SingleDataset, SingleDataset, SingleDataset, SingleDataset]
        Datasets of coordinates grouped as y(x), z(x), z(y) and z(x,y).
    """
    q_array = source["q_vectors"][shell_key]["q_vectors"] * measure(
        1.0,
        iunit="1/nm",
    ).toval("1/ang")
    return projection_datasets_from_qarray(q_array)


def projection_datasets_from_qarray(
    q_array: npt.NDArray[float],
    filename: str | None = None,
) -> tuple[SingleDataset, SingleDataset, SingleDataset, SingleDataset]:
    """Convert a q vector array to datasets of Cartesian coordinates.

    Parameters
    ----------
    q_array : npt.NDArray[float]
        A (3,N) array of reciprocal space vectors.
    filename : str | None, optional
        Name of the file to be shown in plot details, by default None

    Returns
    -------
    tuple[SingleDataset, SingleDataset, SingleDataset, SingleDataset]
        Datasets of coordinates grouped as y(x), z(x), z(y) and z(x,y).
    """
    projection_ab = SingleDataset(
        "q$_y$ vs q$_x$",
        None,
        linestyle="none",
        marker="o",
        data=q_array[1, :],
        plot_axes={"q_x": q_array[0, :]},
        axes_units={"q_x": "1/ang"},
        data_unit="1/ang",
        optional_filename=filename,
    )
    projection_ac = SingleDataset(
        "q$_z$ vs q$_x$",
        None,
        linestyle="none",
        marker="v",
        data=q_array[2, :],
        plot_axes={"q_x": q_array[0, :]},
        axes_units={"q_x": "1/ang"},
        data_unit="1/ang",
        optional_filename=filename,
    )
    projection_bc = SingleDataset(
        "q$_z$ vs q$_y$",
        None,
        linestyle="none",
        marker="s",
        data=q_array[2, :],
        plot_axes={"q_y": q_array[1, :]},
        axes_units={"q_y": "1/ang"},
        data_unit="1/ang",
        optional_filename=filename,
    )
    full_vectors = SingleDataset(
        "q$_z$ in 3D",
        None,
        linestyle="none",
        marker="o",
        data=q_array[2, :],
        plot_axes={"q_x": q_array[0, :], "q_y": q_array[1, :]},
        axes_units={"q_x": "1/ang", "q_y": "1/ang"},
        data_unit="1/ang",
        optional_filename=filename,
    )
    return projection_ab, projection_ac, projection_bc, full_vectors


def vector_q_statistics_datasets(
    source: h5py.File | QVectorsConfigurator,
    main_dset: str = "vector_generator",
    q_bin_limits: npt.NDArray[float] | None = None,
) -> tuple[SingleDataset, SingleDataset]:
    """Create plottable SingleDataset instances showing |q| of generated vectors.

    Parameters
    ----------
    source : h5py.File | QVectorsConfigurator
        An object containing vector parameters: configurator or an .mda file.
    main_dset : str, optional
        Name of the group with q vector shells, by default "vector_generator".
    q_bin_limits : npt.NDArray[float], optional
        Bin limits for the |q| histogram. If not given, it will be determined from |q| values.

    Returns
    -------
    Iterable[SingleDataset]
        1D array of vector count vs. |q|, 2D histogram of q vector counts per shell.
    """
    if isinstance(source, h5py.File):
        filename = source.filename
        parent_dset = source[main_dset]
        qvals = parent_dset["q"][:]
        nshells = len(qvals)
        valid_shells = [
            index
            for index in range(nshells)
            if len(parent_dset[f"shell_{index}/qvector_array"][0])
        ]
        modq_per_shell = [shell_to_modq(n, parent_dset) for n in valid_shells]
        available_vectors = np.array([len(qvecs) for qvecs in modq_per_shell])

        def q_data(elem: str) -> Generator:
            for index in valid_shells:
                yield parent_dset[f"shell_{index}/{elem}"]

        if all(
            "weights" in parent_dset[f"shell_{shell_index}"]
            for shell_index in valid_shells
        ):
            vec_weights = [dat[:] for dat in q_data("weights")]
            if "n_q_vectors" in parent_dset and "n_q_found" in parent_dset:
                used = np.array(parent_dset["n_q_vectors"])
                found = np.array(parent_dset["n_q_found"])
            else:
                used = np.array([len(dat) for dat in q_data("weights")])
                found = np.array([sum(dat[:]) for dat in q_data("weights")])
            available_vectors = np.vstack((found, used)).T
        else:
            vec_weights = [np.ones_like(modq_shell) for modq_shell in modq_per_shell]
    elif isinstance(source, QVectorsConfigurator):
        filename = None
        qvals = np.array([float(x) for x in source["q_vectors"]])
        valid_shells = [
            index
            for index in range(len(qvals))
            if source["q_vectors"][qvals[index]] is not None
        ]
        nshells = len(valid_shells)

        def q_data(elem: str) -> Generator:
            for index in valid_shells:
                yield source["q_vectors"][qvals[index]][elem]

        modq_per_shell = [np.linalg.norm(dat, axis=0) for dat in q_data("q_vectors")]
        available_vectors = np.array(
            [
                (
                    n_found,
                    n_used,
                )
                for n_found, n_used in zip(
                    q_data("n_q_found"), q_data("n_q_vectors"), strict=False
                )
            ],
        )
        vec_weights = [dat[:] for dat in q_data("weights")]
    if q_bin_limits is None:
        qmin, qmax = np.min(modq_per_shell[0]), np.max(modq_per_shell[-1])
        q_step = np.mean(np.abs(np.diff(qvals))) if len(qvals) > 1 else 0.1
        bin_width = 0.4 * np.min([np.std(one_shell) for one_shell in modq_per_shell])
        common_bins = qvector_binning_general(qmin, qmax, q_step, bin_width, 10)
    else:
        common_bins = q_bin_limits
    if np.any(common_bins < 0):
        start_index = np.argmax(common_bins >= 0) - 1
        if start_index >= 0:
            common_bins = common_bins[start_index:]
    qmod_histograms = [np.histogram(qmods, common_bins)[0] for qmods in modq_per_shell]
    stacked_histograms = np.vstack(qmod_histograms)
    xvals = common_bins[1:] - np.diff(common_bins) / 2
    nvec_per_q = SingleDataset(
        "Available vectors",
        None,
        linestyle=":",
        marker="o",
        data=available_vectors,
        plot_axes={
            "|q|": qvals
            if len(qvals) == len(available_vectors)
            else qvals[valid_shells]
        },
        axes_units={"|q|": "1/nm"},
        optional_filename=filename,
    )
    real_q_ideal_q = SingleDataset(
        r"<|q|> - q$_{target}$",
        None,
        linestyle="-",
        marker=".",
        data=[
            np.concatenate(
                [
                    int(vec_weights[shellindex][vecindex] * WEIGHTS_MULTIPLIER)
                    * list(always_iterable(veclen))
                    for vecindex, veclen in enumerate(
                        modq_per_shell[shellindex] - qvals[shell],
                    )
                ],
            )
            for shellindex, shell in enumerate(valid_shells)
        ],
        plot_axes={"|q|": qvals[valid_shells]},
        axes_units={"|q|": "1/nm"},
        data_unit="1/ang",
        optional_filename=filename,
        uneven_array=True,
    )
    vecs_per_qbin = SingleDataset(
        "Shell population",
        None,
        data=stacked_histograms,
        data_unit="counts",
        plot_axes={"|q|": qvals[valid_shells], "q_bin": xvals},
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
    vector_shell_plotting = Signal(object)

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
            self.populateVectorMenu(self.model(), index, event.globalPos())
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
        """Add actions to a contex menu for .mda files in the plot creator.

        Parameters
        ----------
        menu : QMenu
            The QMenu instance created by contex menu event.
        index : QModelIndex
            Index of the active item in the dataset view.
        """
        for action, method in [("Vector summary", self.plot_vectors)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)
            temp_action.setEnabled(self.model().itemFromIndex(index).has_vectors)
        menu.addSeparator()
        for action, method in [("Delete", self.deleteNode)]:
            temp_action = menu.addAction(action)
            temp_action.triggered.connect(method)

    def populateVectorMenu(
        self,
        model: QAbstractItemModel,
        index: QModelIndex,
        event_pos: QPoint,
    ):
        """Show a menu that allows to visualise a single vector shell.

        This function is meant to exit early if the user clicked on an object
        that is not a q vector shell.
        """
        item = model.itemFromIndex(index)
        text = item.text()
        if "shell" not in text:
            return
        mda_data_structure = model.inner_object(index)
        if "qvector_array" not in mda_data_structure:
            return
        self._qvector_shell = mda_data_structure["qvector_array"][:]
        if not len(self._qvector_shell[0]):
            return
        try:
            self._qvector_weights = mda_data_structure["weights"][:]
        except KeyError:
            self._qvector_weights = np.ones(self._qvector_shell.shape[1])
        self._qvector_filename = mda_data_structure.file.filename
        menu = QMenu()
        temp_action = menu.addAction("Vector positions")
        temp_action.triggered.connect(self.plot_vector_shell)
        menu.exec_(event_pos)

    @Slot()
    def deleteNode(self):
        """Delete the selected file from the tree view."""
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

    def on_select_dataset(self, index: QModelIndex):
        """Respond to the user clicking on an item in plot creator's tree view.

        This should collect viewable information about the selected object
        (dataset) and send it to visualiser widgets.

        Parameters
        ----------
        index : QModelIndex
            Index of the selected item in the model.
        """
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
                    ),
                ),
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
        """Create and emit the datasets of |q| statistics in all shells."""
        source_model = self.model()
        index = self.currentIndex()
        mda_data_structure = source_model.parent_object(index)
        file = mda_data_structure._file
        LOG.debug("Running plot_vectors on file %s", file.filename)
        model = PlottingContext()
        _, qvector_params = json.loads(file["metadata/inputs/q_vectors"][0])
        modq_binning = qvector_binning_from_dict(qvector_params)
        for qvec_dataset in vector_q_statistics_datasets(
            file,
            q_bin_limits=modq_binning,
        ):
            model.add_dataset(qvec_dataset)
        self.fast_plotting_vectors.emit(model)

    def plot_vector_shell(self):
        """Create and emit datasets with vector positions in a single shell."""
        new_model = PlottingContext()
        for dataset in projection_datasets_from_qarray(
            self._qvector_shell,
            self._qvector_filename,
        ):
            new_model.add_dataset(dataset)
        for dataset in angular_datasets_from_qarray(
            self._qvector_shell,
            self._qvector_weights,
            self._qvector_filename,
        ):
            new_model.add_dataset(dataset)
        self.vector_shell_plotting.emit(new_model)

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
            html.escape(description),
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
