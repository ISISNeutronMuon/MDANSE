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

from typing import TYPE_CHECKING, Dict, List
import os
import itertools

if TYPE_CHECKING:
    import h5py

import numpy as np

from qtpy.QtCore import Slot, Signal, QObject, QModelIndex, Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE_GUI.Session.LocalSession import unit_lookup


class SingleDataset:

    def __init__(self, name: str, source: "h5py.File"):
        self._name = name
        self._filename = source.filename
        self._curves = {}
        self._curve_labels = {}
        self._planes = {}
        bare_name = os.path.split(self._filename)[-1]
        self._labels = {
            "minimal": name,
            "medium": f"{bare_name}:{name}",
            "full": f"{self._filename}:{name}",
        }
        self._valid = True
        try:
            self._data = source[name][:]
        except KeyError:
            print(f"{name} is not a data set in the file")
            self._valid = False
            return
        except TypeError:
            self._valid = False
            print(f"{name} is not plottable")
            return
        self._data_unit = source[name].attrs["units"]
        self._n_dim = len(self._data.shape)
        self._axes_tag = source[name].attrs["axis"]
        self._axes = {}
        self._axes_units = {}
        for axis_name in self._axes_tag.split("|"):
            aname = axis_name.strip()
            if aname == "index":
                self._axes[aname] = range(len(self._data))
                self._axes_units[aname] = "N/A"
            else:
                self._axes[aname] = source[aname][:]
                self._axes_units[aname] = source[aname].attrs["units"]

    def available_x_axes(self) -> List[str]:
        return list(self._axes_units.values())

    def longest_axis(self) -> str:
        length = -1
        best_unit = "none"
        best_axis = "none"
        for aname, aunit in self._axes_units.items():
            xaxis = self._axes[aname]
            xlen = len(xaxis)
            if xlen > length:
                length = xlen
                best_unit = aunit
                best_axis = aname
        return best_unit, best_axis

    def curves_vs_axis(self, axis_unit: str) -> List[np.ndarray]:
        found = -1
        total_ndim = len(self._data.shape)
        data_shape = self._data.shape
        for aname, aunit in self._axes_units.items():
            if aunit == axis_unit:
                xaxis = self._axes[aname]
                xlen = len(xaxis)
                for dim in range(total_ndim):
                    if xlen == self._data.shape[dim]:
                        found = dim
                        break
        slicer = []
        indexer = []
        for dim in range(total_ndim):
            if dim == found:
                slicer.append([slice(None)])
                # indexer.append([None])
            else:
                slicer.append(np.arange(data_shape[dim]))
                indexer.append(np.arange(data_shape[dim]))
        indices = list(itertools.product(*indexer))
        slicers = list(itertools.product(*slicer))
        for n in range(len(indices)):
            self._curves[tuple(indices[n])] = self._data[slicers[n]].squeeze()
            self._curve_labels[tuple(indices[n])] = str(tuple(indices[n]))
        return self._curves
        # slicer = tuple(slicer)
        # temp = self._data[slicer].squeeze()
        # for line in temp:
        #     if len(line) != xlen:
        #         print("Wrong data length in the curves_vs_axis method of PlottingContext")
        # return temp


class SingleCurve:

    def __init__(self, data_name: str, file_name: str, *args, **kwargs):
        self._name = data_name
        self._filename = file_name
        self._curve = []
        self._x_axis = []
        self._y_axis = None
        self._z_axis = None
        bare_name = os.path.split(self._filename)[-1]
        self._labels = {
            "minimal": data_name,
            "medium": f"{bare_name}:{data_name}",
            "full": f"{file_name}:{data_name}",
        }
        self._label = self._labels["medium"]
        self._units = {"data": "arbitrary", "x": None, "y": None, "z": None}
        self._colour = "#000000"
        self._line = "-"

    def set_data(self, array: np.ndarray, unit: str):
        self._curve = array
        self._units["data"] = unit

    def set_x_axis(self, array: np.ndarray, unit: str):
        self._x_axis = array
        self._units["x"] = unit

    def set_y_axis(self, value: float, unit: str):
        self._y_axis = value
        self._units["y"] = unit

    def set_z_axis(self, value: float, unit: str):
        self._z_axis = value
        self._units["z"] = unit

    def standard_items(self, key: int) -> List["QStandardItem"]:
        result = []
        for val in []:
            item = QStandardItem(str(val))
            item.setData(key, role=Qt.ItemDataRole.UserRole)
            result.append(item)
        return result


class PlottingContext(QStandardItemModel):

    needs_an_update = Signal()

    def __init__(self, *args, unit_preference=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._datasets = {}
        self._current_axis = [None, None, None]
        self._figure = None
        self._ndim_lowest = 1
        self._ndim_highest = 3
        self._all_xunits = []
        self._best_xunits = []
        if unit_preference is None:
            self._unit_preference = {}
        else:
            self._unit_preference = unit_preference
        self.setHorizontalHeaderLabels(
            ["Dataset", "Trajectory", "Size", "Unit", "Use it?"]
        )

    @Slot(object)
    def accept_external_data(self, other: "PlottingContext"):
        """Crucial slot for transferring data
        between tabs. DataPlotter will send the datasets
        into this slot."""
        for dataset in other._datasets.values():
            self.add_dataset(dataset)
        self.set_axes()

    @Slot(dict)
    def accept_units(self, units: Dict):
        """Crucial slot for transferring data
        between tabs. DataPlotter will send the datasets
        into this slot."""
        self._unit_preference = units
        self.set_axes()

    def get_conversion_factor(self, unit):
        quantity = unit_lookup.get(unit, "unknown")
        if quantity in self._unit_preference:
            new_unit = self._unit_preference[quantity]
        else:
            new_unit = unit
        return new_unit

    def datasets(self) -> Dict:
        result = {}
        for row in range(self.rowCount()):
            key = self.index(row, 0).data(role=Qt.ItemDataRole.UserRole)
            useit = (
                self.itemFromIndex(self.index(row, 4)).checkState()
                == Qt.CheckState.Checked
            )
            if useit:
                result[key] = self._datasets[key]
        return result

    def add_dataset(self, new_dataset: SingleDataset):
        if not new_dataset._valid:
            return
        newkey = f"{new_dataset._filename}:{new_dataset._name}"
        if newkey in self._datasets:
            return
        self._datasets[newkey] = new_dataset
        items = [
            QStandardItem(str(x))
            for x in [
                new_dataset._name,
                new_dataset._filename,
                new_dataset._data.shape,
                new_dataset._data_unit,
                "",
            ]
        ]
        for item in items:
            item.setData(newkey, role=Qt.ItemDataRole.UserRole)
            item.setEditable(False)
        temp = items[4]
        temp.setCheckable(True)
        temp.setCheckState(Qt.CheckState.Checked)
        self.itemChanged.connect(self.needs_an_update)
        # test for possible nested items
        best_axis = new_dataset.longest_axis()
        curves = new_dataset.curves_vs_axis(best_axis[0])
        if len(curves) > 1:
            counter = 1
            for indices, curve in curves.items():
                temp = SingleCurve(new_dataset._name, new_dataset._filename)
                temp.set_data(curve, new_dataset._data_unit)
                temp.set_x_axis(new_dataset._axes[best_axis[1]], best_axis[0])
                # optionally, we should set y and z as well
                subitems = temp.standard_items(newkey + f":{counter}")
                items[0].appendRow(subitems)
                counter += 1
        else:
            print("No curves!")
        self.appendRow(items)

    def set_axes(self):
        if len(self._datasets) == 0:
            return
        all_axes = []
        all_dimensions = []
        longest_axes = []
        unit_to_axname = {}
        for dataset in self._datasets.values():
            n_dimensions = dataset._n_dim
            if n_dimensions not in all_dimensions:
                all_dimensions.append(n_dimensions)
            best_units, best_axis = dataset.longest_axis()
            unit_to_axname[best_units] = best_axis
            for unit in dataset._axes_units.values():
                if unit not in all_axes:
                    all_axes.append(unit)
            if best_units not in longest_axes:
                longest_axes.append(best_units)
        self._ndim = 1
        self._ndim_highest = np.max(all_dimensions)
        self._ndim_lowest = np.min(all_dimensions)
        self._best_xunits = longest_axes
        self._all_xunits = all_axes
        self._unit_to_axname = unit_to_axname
        # self.needs_an_update.emit()
        return "Configured!"

    @Slot()
    def clear(self) -> None:
        result = super().clear()
        self._datasets = {}
        return result

    @Slot(QModelIndex)
    def delete_dataset(self, index: QModelIndex):
        dkey = index.data(role=Qt.ItemDataRole.UserRole)
        self.removeRow(index.row())
        self._datasets.pop(dkey, None)
