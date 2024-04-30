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

import abc
import os
import json

import numpy as np

import h5py

from qtpy import QtCore, QtGui

from MDANSE.Framework.Units import measure, UnitError


json_decoder = json.decoder.JSONDecoder()


class DataItemError(Exception):
    pass


class DataTreeModelError(Exception):
    pass


class NodeItem:
    def __init__(self, path, is_group):
        """Constructor.

        Args:
            path (str): the path of the data stored in the node
            is_group (bool): True if the node is a group, False if it is a terminal node
        """
        self._group = os.path.dirname(path) if path is not None else None

        self._name = os.path.basename(path) if path is not None else None

        self._path = path

        self._parent = None

        self._is_group = is_group

        self._children = []

    def get_registered_datasets(self, datasets):
        """Retrieves recursively all the datsets registered under this node.

        Args:
            datasets (list): the registered datasets.
        """
        for child in self._children:
            if child.is_group():
                child.get_registered_datasets(datasets)
            else:
                datasets.append(child.path)

    def add_child(self, child):
        """Append a child to the current node.

        Args:
            child (NodeItem): the child to append
        """
        child._parent = self
        self._children.append(child)

    def child(self, row):
        """Return the child node matching a given row.

        Args:
            row (int): the row

        Returns:
            NodeItem: the child node
        """
        return self._children[row]

    @property
    def children(self):
        """Returns the list of children of this node.

        Returns:
            list of NodeItem: the children
        """
        return self._children

    def child_count(self):
        """Return the number of child nodes of this node.

        Returns:
            int: the number of child nodes
        """
        return len(self._children)

    def column_count(self):
        """Return the number of columns of this node.

        Returns:
            int: the number of columns
        """
        return 1

    def get_data_root_item(self):
        """Returns the data node at the root of this node.

        Returns:
            DataItem: the data node
        """
        if self._parent is None:
            return None

        if isinstance(self, DataItem):
            return self
        else:
            return self.parent.get_data_root_item()

    @property
    def group(self):
        """Returns the group of this node.

        Returns:
            str: the group
        """
        return self._group

    def is_group(self):
        """Returns whether or not this node is a group.

        Returns:
            bool: True if this node is a group, False otherwise
        """
        return self._is_group

    @property
    def name(self):
        """Returns the name of this node.

        Returns:
            str: the name
        """
        return self._name

    @property
    def parent(self):
        """Returns the parent node of this node.

        Returns:
            NodeItem: the parent node
        """
        return self._parent

    @property
    def path(self):
        """Returns the path of this node.

        Returns:
            str: the path
        """
        return self._path

    def remove_child(self, row):
        """Remove a child of this node.

        Args:
            row (int): the index of the child to remove
        """
        del self._children[row]

    def row(self):
        """Return the row of this item regarding its parent.

        Returns:
            int: the row
        """
        return self._parent._children.index(self) if self._parent else 0


class DataItem(NodeItem):
    def __del__(self):
        """Deleter of DataItem object."""
        self._file.close()

    def _build_index_variable(self, size):
        """Build an index variable of a given size. An index variable is a variable used to
        build axis of type 'index'.

        Args:
            size (int): the size of the index variable

        Returns:
            dict: the information about the index variable
        """
        data = np.arange(size, dtype=np.float64)
        info = {}
        info["variable"] = "index"
        info["axis"] = None
        info["units"] = "au"
        info["dimension"] = data.ndim
        info["shape"] = data.shape
        info["path"] = None
        info["data"] = data
        return info

    def get_axis_data(self, variable_info):
        """Gets the axis data info of a given variable.

        Args:
            variable_info (dict): the information about the variable for which the axis should be obtained.

        Returns:
            list of dict: the axis information for each axis of the given variable
        """
        registered_datasets = []
        self.get_registered_datasets(registered_datasets)

        axis = [v for v in variable_info["axis"].split("|") if v]
        shape = variable_info["shape"]

        axis_data = []
        for i, ax in enumerate(axis):
            if ax == "index":
                index_data = self._build_index_variable(shape[i])
                axis_data.append(index_data)
            else:
                for d in registered_datasets:
                    dinfo = self.get_dataset_info(d, add_data=True)
                    if dinfo["variable"] == ax:
                        axis_data.append(dinfo)
                        break
                else:
                    index_data = self._build_index_variable(shape[i])
                    axis_data.append(index_data)
        return axis_data


class HDFDataItem(DataItem):
    def __init__(self, filename):
        """Constructor.

        Args:
            filename (str): the HDF filename
        """
        try:
            file = h5py.File(filename, "r")
        except Exception as e:
            raise DataTreeModelError(str(e))
        else:
            self._filename = filename
            self._file = file
            self._filename = filename
            self._file = file
            self._group = None
            self._name = os.path.basename(filename)
            self._path = filename
            self._parent = None
            self._is_group = True
            self._children = []
            self._metadata = {}

        self.check_metadata()
        self._parse(self, self._file)

    def check_metadata(self):
        meta_dict = {}

        def put_into_dict(name, obj):
            try:
                string = obj[:][0].decode()
            except:
                print(f"Decode failed for {name}: {obj}")
            else:
                try:
                    meta_dict[name] = json_decoder.decode(string)
                except ValueError:
                    meta_dict[name] = string

        try:
            meta = self._file["metadata"]
        except KeyError:
            return
        else:
            meta.visititems(put_into_dict)
        self._metadata = meta_dict

    def _parse(self, node, group):
        """Retrieve recursively all the variables stored in a HDF file and build the tree out of this.

        Args:
            node (NodeItem): the current node
            groupp (bool): True if this node is a group, False otherwise
        """
        for element in group.values():
            if isinstance(element, h5py.Group):
                sub_node = NodeItem(element.name, True)
                node.add_child(sub_node)
                self._parse(sub_node, element)
            elif isinstance(element, h5py.Dataset):
                path = element.name
                node.add_child(NodeItem(path, False))
            else:
                continue

    def get_dataset_info(self, dataset, add_data=False):
        """Returns the information about a given dataset.

        Args:
            dataset (str): the dataset
            add_data (bool): if True the actual data will be added to the information

        Returns:
            dict: the information about the dataset
        """
        hdf_variable = self._file[dataset]

        info = {}
        info["plottable"] = True
        info["path"] = dataset
        info["status"] = info["path"]
        info["filename"] = self._file.filename
        info["variable"] = os.path.basename(hdf_variable.name)

        # Check units
        try:
            info["units"] = hdf_variable.attrs.get("units", b"au").decode("utf-8")
        except AttributeError:
            info["units"] = hdf_variable.attrs.get("units", "au")

        try:
            _ = measure(1.0, info["units"], equivalent=True)
        except UnitError:
            info["plottable"] = False
            info["status"] = "unknown unit"

        # Check shape
        info["original_shape"] = hdf_variable.shape
        if hdf_variable.ndim > 1:
            info["shape"] = tuple([s for s in hdf_variable.shape if s > 1])
            if not info["shape"]:
                info["shape"] = (1,)
        elif hdf_variable.ndim == 1:
            info["shape"] = hdf_variable.shape
        else:
            info["shape"] = (1,)

        info["dimension"] = len(info["shape"])
        info["axis"] = hdf_variable.attrs.get(
            "axis", "|".join(["index"] * info["dimension"])
        )

        # Check type
        if np.issubdtype(hdf_variable.dtype, np.number):
            info["type"] = hdf_variable.dtype.name
        else:
            info["type"] = "str"
            info["plottable"] = False
            info["status"] = "invalid data type"

        if add_data:
            if hdf_variable.ndim > 1:
                info["data"] = np.squeeze(hdf_variable[:])
                if not info["data"].shape:
                    info["data"] = np.expand_dims(info["data"], axis=0)
            elif hdf_variable.ndim == 1:
                info["data"] = hdf_variable[:]
            else:
                try:
                    info["data"] = np.expand_dims(hdf_variable[:], axis=0)
                except ValueError:
                    info["data"] = np.array(hdf_variable)

        return info


class DataTreeModel(QtCore.QAbstractItemModel):
    __metaclass__ = abc.ABCMeta

    DatasetInfoRole = QtCore.Qt.ItemDataRole.UserRole

    AxisInfoRole = QtCore.Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (qtpy.QtWidgets.QWidget): the parent of this model
        """
        super(DataTreeModel, self).__init__(parent)

        self._root = NodeItem(None, True)

    def _search_node(self, node, path):
        """Search recursively for a node whose path matches the given path.

        Args:
            node (NodeItem): the current node
            path (str): the path to search
        """
        if node.is_group():
            for child in node.children:
                temp = self._search_node(child, path)
                if temp is not None:
                    return temp
        else:
            if node.path == path:
                return node
        return None

    def add_data(self, filename):
        """Add a data to the model.

        Args:
            filename (str): the filename of the data to add
        """
        ext = os.path.splitext(filename)[1]
        data_tree_item_class = DATA_ITEMS.get(ext, None)
        if data_tree_item_class is None:
            return

        try:
            data_item = data_tree_item_class(filename)
        except DataItemError:
            raise DataTreeModelError(
                f"The file {filename} could not be opened for reading"
            )
        else:
            self._root.add_child(data_item)
            self.layoutChanged.emit()

    def columnCount(self, parent=QtCore.QModelIndex()):
        """Return the number of columns of the model.

        Args:
            parent (qtpy.QtCore.QModelIndex): the parent model

        Returns:
            int: the number of columns
        """
        if parent.isValid():
            return parent.internalPointer().column_count()
        else:
            return self._root.column_count()

    def data(self, index, role):
        """Return the data for a given index and role

        Args:
            index (qtpy.QtCore.QModelIndex): the index
            role (int): the role

        Returns:
            any: the data
        """
        if not index.isValid():
            return None

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            node = index.internalPointer()
            return node.name

        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            node = index.internalPointer()
            if node.is_group():
                return None
            else:
                data_root_item = self.get_data_root_item(node)
                variable_info = data_root_item.get_dataset_info(node.path, False)
                return (
                    QtGui.QColor("black")
                    if variable_info["plottable"]
                    else QtGui.QColor("red")
                )

        elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
            node = index.internalPointer()
            if node.is_group():
                try:
                    metadata = str(node._metadata)
                except:
                    metadata = "No metadata found in the file"
                return node.path + "\n" + metadata
            else:
                data_root_item = self.get_data_root_item(node)
                variable_info = data_root_item.get_dataset_info(node.path, False)
                info = "\n".join([f"{k}: {v}" for k, v in variable_info.items()])
                return info

        elif role == DataTreeModel.DatasetInfoRole:
            node = index.internalPointer()
            if node.is_group():
                return None
            data_root_item = self.get_data_root_item(node)
            variable_info = data_root_item.get_dataset_info(node.path, True)
            return variable_info

        elif role == DataTreeModel.AxisInfoRole:
            node = index.internalPointer()
            if node.is_group():
                return None
            else:
                data_root_item = self.get_data_root_item(node)
                variable_info = data_root_item.get_dataset_info(node.path, False)
                axis_data = data_root_item.get_axis_data(variable_info)
                return axis_data

        else:
            return None

    def get_data_root_item(self, node):
        """Returns the data item of a given node.

        Args:
            node (NodeItem): the node

        Returns:
            DataItem: the data item
        """
        if node.parent == self._root:
            return node
        else:
            return self.get_data_root_item(node.parent)

    def get_index_from_path(self, path):
        """Returns the index of the node matching a given path.

        Args:
            path (str): the path

        Returns:
            qtpy.QtCore.QmodelIndex: the matching index
        """
        node = self._search_node(self._root, path)
        if node is None:
            index = QtCore.QModelIndex()
        else:
            index = self.createIndex(node.row(), 0, node)
        return index

    def index(self, row, column, _parent=None):
        """Return the index of an item matching a given row and column.

        Args:
            row (int): the row
            column (int): the column
            parent (qtpy.QtCore.QModelIndex): the parent of the item

        """
        if not _parent or not _parent.isValid():
            parent = self._root
        else:
            parent = _parent.internalPointer()

        if not QtCore.QAbstractItemModel.hasIndex(self, row, column, _parent):
            return QtCore.QModelIndex()

        child = parent.child(row)
        if child:
            return QtCore.QAbstractItemModel.createIndex(self, row, column, child)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        """Return the index of the parent of an item matching a given index.

        Args:
            qtpy.QtCore.QModelIndex: the index of the item

        Returns:
            qtpy.QtCOre.QmodelIndex: the index of the parent
        """
        if index.isValid():
            p = index.internalPointer().parent
            if p:
                return QtCore.QAbstractItemModel.createIndex(self, p.row(), 0, p)
        return QtCore.QModelIndex()

    def removeRow(self, row, parent):
        """Remove a row of the model according to a given parent.

        Args:
            row (int): the row to remove
            parent (atpy.QtCore.QModelIndex): the index of the parent
        """
        if not parent.isValid():
            return

        parent_node = parent.internalPointer()
        if parent_node != self._root:
            return

        self.beginRemoveRows(parent, row, row)
        parent_node.remove_child(row)
        self.endRemoveRows()

    def rowCount(self, parent):
        """Return the number of rows under a given parent.

        Args:
            parent (qtpy.QtCore.QModelIndex): the parent index

        Returns:
            int: the number of rows
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()

        return parent_item.child_count()


DATA_ITEMS = {
    ".mda": HDFDataItem,
    ".hdf": HDFDataItem,
    ".h5": HDFDataItem,
    ".nxs": HDFDataItem,
}
