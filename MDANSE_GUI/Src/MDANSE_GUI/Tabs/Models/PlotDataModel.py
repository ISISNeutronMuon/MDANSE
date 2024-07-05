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
import logging
from abc import abstractmethod

import h5py

from qtpy.QtCore import QObject, Slot, Signal, QMutex, QModelIndex, Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE_GUI.Session.LocalSession import json_decoder


LOG = logging.getLogger("MDANSE")


class BasicPlotDataItem(QStandardItem):
    """Each item in the PlotDataModel is a BasicPlotDataItem.
    Since there are only two levels of nesting in the data tree,
    there are two types of item we will use, both of them
    derived from BasicPlotDataItem
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_type = "generic"

    @abstractmethod
    def data_path(self):
        pass

    @abstractmethod
    def file_number(self):
        pass

    def populate(self, file):
        for key in file.keys():
            try:
                file[key]
            except Exception as e:
                LOG.error(f"error {e} when accessing file[{key}]")
            else:
                child = DataSetItem()
                child.setText(key)
                child.setData(key, role=Qt.ItemDataRole.DisplayRole)
                child.setData(key, role=Qt.ItemDataRole.UserRole)
                try:
                    file[key][:]
                except:
                    child._item_type = "group"
                self.appendRow(child)


class DataSetItem(BasicPlotDataItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_type = "dataset"

    def data_path(self) -> str:
        parent_path = self.parent().data_path()
        own_path = self.data(role=Qt.ItemDataRole.UserRole)
        return "/".join([parent_path, own_path])

    def file_number(self) -> int:
        return self.parent().file_number()


class DataFileItem(BasicPlotDataItem):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_type = "file"

    def data_path(self) -> str:
        return ""

    def file_number(self) -> int:
        return self.data(role=Qt.ItemDataRole.UserRole)


class MDADataStructure:

    def __init__(self, filename: str):
        self._file = h5py.File(filename)
        self.check_metadata()
        self.find_information()

    def close(self):
        self._file.close()

    def find_information(self):
        self._main_dataset = ""
        self._components = []
        self._axis_datasets = []
        self._supporting_datasets = []

    def check_metadata(self):
        meta_dict = {}

        def put_into_dict(name, obj):
            try:
                string = obj[:][0]
            except TypeError:
                try:
                    string = obj[0]
                except TypeError:
                    return
            try:
                string = string.decode()
            except KeyError:
                LOG.error(f"Decode failed for {name}: {obj}")
                meta_dict[name] = str(obj)
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


class PlotDataModel(QStandardItemModel):
    """Meant to be used with DoublePanel, GeneralView
    and ItemVisualiser. It stores elements and emits
    them to the ItemVisualiser."""

    error = Signal(str)
    all_elements = Signal(object)

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.mutex = QMutex()
        self._nodes = {}
        self._next_number = 0

    @Slot(str)
    def add_file(self, filename: str):
        try:
            new_datafile = MDADataStructure(filename)
        except Exception as e:
            LOG.error(f"Invalid: {str(e)}")
        else:
            self._nodes[self._next_number] = new_datafile
            new_item = DataFileItem()
            new_item.setData(f"{filename}", role=Qt.ItemDataRole.DisplayRole)
            new_item.setData(self._next_number, role=Qt.ItemDataRole.UserRole)
            self._next_number += 1
            self.appendRow(new_item)
            new_item.populate(new_datafile._file)

    def inner_object(self, index: QModelIndex) -> MDADataStructure:
        model_item = self.itemFromIndex(index)
        number = model_item.file_number()
        data_path = model_item.data_path()
        data_structure = self._nodes[number]
        if data_path:
            return data_structure._file[data_path]
        return data_structure

    def removeRow(self, row: int, parent: QModelIndex = None):
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
