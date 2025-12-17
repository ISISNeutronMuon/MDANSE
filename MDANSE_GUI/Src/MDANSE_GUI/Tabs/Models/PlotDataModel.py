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

from abc import abstractmethod
from pathlib import Path
from typing import TypeVar

import h5py
from qtpy.QtCore import QModelIndex, QMutex, QObject, Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Framework.Formats.HDFFormat import check_metadata
from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.RecentFiles import RecentFiles

Self = TypeVar("Self", bound="BasicPlotDataItem")
EXCLUDE = {"metadata"}


class BasicPlotDataItem(QStandardItem):
    """Each item in the PlotDataModel is a BasicPlotDataItem."""

    def __init__(self, *args, data_parent: Self | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_parent = data_parent
        self._item_type = "generic"
        self.has_vectors = False

    @abstractmethod
    def data_path(self):
        """Return the path to the object inside the HDF5 file."""
        pass

    @abstractmethod
    def file_number(self):
        """Return the model index of the source HDF5 file."""
        pass

    @property
    def child_path(self):
        """Recursively build the HDF5 path to this object."""
        if self.data_parent is None:
            return ""
        else:
            return f"{self.data_parent.child_path}/{self.text()}"

    def recursive_children(self, recursion_limit: int = 1) -> list[BasicPlotDataItem]:
        """Return a list composed of this node and all its children.

        Parameters
        ----------
        recursion_limit : int, optional
            Number of levels of nesting to search, unlimited on negative values, by default 1

        Returns
        -------
        list[BasicPlotDataItem]
            list of this node and all the children nodes within the recursion (depth) limit
        """
        result = [self]
        if recursion_limit == 0:
            return result
        for child_row in range(self.rowCount()):
            child = self.child(child_row, 0)
            if recursion_limit and child:
                result += child.recursive_children(recursion_limit - 1)
        return result

    def populate(self, data: h5py.File | h5py.Group):
        """Create model items for the children datasets from the HDF5 file."""
        self.has_vectors = "vector_generator" in data
        for key in data.keys() - EXCLUDE:
            try:
                data[key]
            except Exception as e:
                LOG.error(f"error {e} when accessing data[{key}]")
                continue

            child = DataSetItem(data_parent=self)
            child.setText(key)
            child.setData(key, role=Qt.ItemDataRole.DisplayRole)
            child.setData(key, role=Qt.ItemDataRole.UserRole)
            try:
                data[key][:]
            except Exception:
                child.populate(data[key])
                child._item_type = "group"
            self.appendRow(child)


class DataSetItem(BasicPlotDataItem):
    """A specialised model item for an end node (dataset)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_type = "dataset"

    def data_path(self) -> str:
        """Recursively build the HDF5 path to this dataset."""
        parent_path = self.parent().data_path()
        own_path = self.data(role=Qt.ItemDataRole.UserRole)
        return f"{parent_path}/{own_path}"

    def file_number(self) -> int:
        """Return the model index of the source data file."""
        return self.parent().file_number()


class DataFileItem(BasicPlotDataItem):
    """A specialised item for a top-level node (data file) in the model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_type = "file"

    def data_path(self) -> str:
        """Return an empty string, since this item is not a dataset."""
        return ""

    def file_number(self) -> int:
        """Return the inner model index of the data file from _nodes dictionary."""
        return self.data(role=Qt.ItemDataRole.UserRole)


class MDADataStructure:
    """Loads plotting-related information from an MDA file."""

    def __init__(self, filename: str):
        self._file = h5py.File(filename)
        self._metadata = check_metadata(self._file)
        # Ensure only mda type file are loaded in Plot Creator Tab
        output_metadata = self._metadata["inputs/output_files"]
        if (
            not isinstance(output_metadata[1], list)
            or "MDAFormat" not in output_metadata[1]
        ):
            self.close()
            raise ValueError(f"Not a .mda type file {filename}")

    def close(self):
        """Close the HDF5 file."""
        self._file.close()


class PlotDataModel(QStandardItemModel):
    """Stores plottable items from an MDA file.

    Meant to be used with DoublePanel, GeneralView and ItemVisualiser.
    It stores elements and emits them to the ItemVisualiser.
    """

    DEFAULT_JSON_PATH = (
        PLATFORM.application_directory() / "recent_plot_selection_file.json"
    )
    MAX_NUMBER_RECENT_FILES = 10  # maximum number of recent files to store
    PLACEHOLDER_STRING = "Recently used result files (.mda)"
    recent_files = RecentFiles(
        DEFAULT_JSON_PATH,
        MAX_NUMBER_RECENT_FILES,
        PLACEHOLDER_STRING,
    )

    error = Signal(str)
    all_elements = Signal(object)
    finished_loading = Signal(int)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._nodes = {}
        self._next_number = 0

    @Slot(str)
    def add_file(self, filename: str):
        """Add to the model all the plottable datasets from a file.

        Parameters
        ----------
        filename : str
            path to an MDA file

        """
        try:
            new_datafile = MDADataStructure(filename)
        except Exception as e:
            LOG.error("Invalid: %s", e)
        else:
            self._nodes[self._next_number] = new_datafile
            new_item = DataFileItem()
            new_item.setData(f"{Path(filename).name}", role=Qt.ItemDataRole.DisplayRole)
            new_item.setData(self._next_number, role=Qt.ItemDataRole.UserRole)
            self.appendRow(new_item)
            new_item.populate(new_datafile._file)
            self.finished_loading.emit(self._next_number)
            self.recent_files.store_recently_used_filename(filename)
            self._next_number += 1

    def inner_object(self, index: QModelIndex) -> MDADataStructure | h5py.Dataset:
        """For a Qt model index, return its corresponding HDF5 object.

        Parameters
        ----------
        index : QModelIndex
            Index of the model item from the Qt model.

        Returns
        -------
        MDADataStructure | h5py.Dataset
            Either a wrapper around the MDA file, or a dataset from the file.

        """
        model_item = self.itemFromIndex(index)
        if model_item is None:
            return
        number = model_item.file_number()
        data_path = model_item.data_path()
        data_structure = self._nodes[number]
        if data_path:
            return data_structure._file[data_path]
        return data_structure

    def parent_object(self, index: QModelIndex) -> MDADataStructure:
        """For a Qt index of a dataset, return the wrapper object of the HDF5 file.

        Parameters
        ----------
        index : QModelIndex
            Index of the model item from the Qt model.

        Returns
        -------
        MDADataStructure
            A wrapper around the MDA file.

        """
        model_item = self.itemFromIndex(index)
        number = model_item.file_number()
        return self._nodes[number]

    def removeRow(self, row: int, parent: QModelIndex = None):
        """Delete a row from the model."""
        self.mutex.lock()
        try:
            node_number = self.item(row).data(role=Qt.ItemDataRole.UserRole)
        except AttributeError:
            return
        data_object = self._nodes.pop(node_number)
        data_object.close()
        if parent is None:
            super().removeRow(row)
        else:
            super().removeRow(row, parent)
        self.mutex.unlock()
