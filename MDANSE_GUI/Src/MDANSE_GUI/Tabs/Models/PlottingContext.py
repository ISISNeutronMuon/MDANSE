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
from matplotlib.markers import MarkerStyle
from matplotlib.lines import lineStyles
from matplotlib import rcParams
from matplotlib.colors import to_hex as mpl_to_hex
import matplotlib.pyplot as mpl
from qtpy.QtCore import Slot, Signal, QModelIndex, Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem, QColor

from MDANSE.MLogging import LOG


def get_mpl_markers():
    unique_keys = list(set(MarkerStyle.markers.keys()))
    filtered_markers = {
        key: MarkerStyle.markers[key]
        for key in unique_keys
        if key not in ["", " ", "none"] + [str(x) for x in range(10)]
    }
    return filtered_markers


def get_mpl_lines():
    filtered_line_styles = {
        key: value for key, value in lineStyles.items() if key not in ["", " "]
    }
    return filtered_line_styles


def get_mpl_colours():
    cycler = rcParams["axes.prop_cycle"]
    colours = cycler.by_key()["color"]
    return [mpl_to_hex(col) for col in colours]


class SingleDataset:

    def __init__(self, name: str, source: "h5py.File"):
        self._name = name
        self._filename = source.filename
        self._curves = {}
        self._curve_labels = {}
        self._planes = {}
        self._plane_labels = {}
        self._data_limits = None
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
            LOG.debug(f"{name} is not a data set in the file")
            self._valid = False
            return
        except TypeError:
            self._valid = False
            LOG.debug(f"{name} is not plottable")
            return
        self._data_unit = source[name].attrs["units"]
        self._n_dim = len(self._data.shape)
        self._axes_tag = source[name].attrs["axis"]
        self._axes = {}
        self._axes_units = {}
        for ax_number, axis_name in enumerate(self._axes_tag.split("|")):
            aname = axis_name.strip()
            if aname == "index":
                self._axes[aname + str(ax_number)] = np.arange(len(self._data))
                self._axes_units[aname + str(ax_number)] = "N/A"
            else:
                self._axes[aname] = source[aname][:]
                self._axes_units[aname] = source[aname].attrs["units"]

    def set_data_limits(self, limit_string: str):
        complete_subset_list = []
        for token in limit_string.split(";"):
            if ":" in token:
                try:
                    slice_parts = [int(x) for x in token.split(":")]
                except:
                    continue
                if len(slice_parts) < 4:
                    complete_subset_list += list(range(*slice_parts))
            elif "-" in token:
                try:
                    slice_parts = [int(x) for x in token.split("-")]
                except:
                    continue
                if len(slice_parts) == 2:
                    complete_subset_list += list(range(slice_parts[0], slice_parts[1]))
            elif "," in token:
                try:
                    slice_parts = [int(x) for x in token.split(",")]
                except:
                    continue
                complete_subset_list += list(slice_parts)
            else:
                try:
                    complete_subset_list += [int(token)]
                except:
                    continue
        if len(complete_subset_list) == 0:
            self._data_limits = None
        else:
            self._data_limits = np.unique(complete_subset_list).astype(int)

    def available_x_axes(self) -> List[str]:
        return list(self._axes_units.keys())

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
        self._curves = {}
        self._curve_labels = {}
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
            if self._data_limits is not None:
                if n in self._data_limits:
                    self._curves[tuple(indices[n])] = self._data[slicers[n]].squeeze()
                    self._curve_labels[tuple(indices[n])] = str(tuple(indices[n]))
            else:
                self._curves[tuple(indices[n])] = self._data[slicers[n]].squeeze()
                self._curve_labels[tuple(indices[n])] = str(tuple(indices[n]))
        return self._curves
        # slicer = tuple(slicer)
        # temp = self._data[slicer].squeeze()
        # for line in temp:
        #     if len(line) != xlen:
        #         print("Wrong data length in the curves_vs_axis method of PlottingContext")
        # return temp

    def planes_vs_axis(self, axis_number: int) -> List[np.ndarray]:
        self._planes = {}
        self._plane_labels = {}
        found = -1
        total_ndim = len(self._data.shape)
        if total_ndim == 1:
            return
        elif total_ndim == 2:
            return self._data
        data_shape = self._data.shape
        number_of_planes = data_shape[axis_number]
        perpendicular_axis = None
        perpendicular_axis_name = ""
        slice_def = []
        for number, (axis_name, axis_array) in enumerate(self._axes.items()):
            if number == axis_number:
                slice_def.append(0)
                perpendicular_axis = axis_array
                perpendicular_axis_name = axis_name
            else:
                slice_def.append(slice(None))
        for plane_number in range(number_of_planes):
            if self._data_limits is not None:
                if plane_number in self._data_limits:
                    fixed_argument = perpendicular_axis[plane_number]
                    slice_def[axis_number] = plane_number
                    data = self._data[tuple(slice_def)]
                    self._planes[plane_number] = data
                    self._plane_labels[plane_number] = (
                        f"{perpendicular_axis_name}={fixed_argument}"
                    )
            else:
                fixed_argument = perpendicular_axis[plane_number]
                slice_def[axis_number] = plane_number
                data = self._data[tuple(slice_def)]
                self._planes[plane_number] = data
                self._plane_labels[plane_number] = (
                    f"{perpendicular_axis_name}={fixed_argument}"
                )


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


plotting_column_labels = [
    "Dataset",
    "Trajectory",
    "Size",
    "Unit",
    "Main axis",
    "Use it?",
    "Colour",
    "Line style",
    "Marker",
]
plotting_column_index = {
    label: number for number, label in enumerate(plotting_column_labels)
}


class PlottingContext(QStandardItemModel):

    needs_an_update = Signal()

    def __init__(self, *args, unit_lookup=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._datasets = {}
        self._current_axis = [None, None, None]
        self._figure = None
        self._ndim_lowest = 1
        self._ndim_highest = 3
        self._all_xunits = []
        self._best_xunits = []
        self._colour_list = get_mpl_colours()
        self._last_colour_list = get_mpl_colours()
        self._colour_map = kwargs.get("colormap", "viridis")
        self._last_colour = 0
        self._unit_lookup = unit_lookup
        self.setHorizontalHeaderLabels(plotting_column_labels)

    def generate_colour(self, number: int):
        return self._colour_list[number % len(self._colour_list)]

    def next_colour(self):
        colour = self.generate_colour(self._last_colour)
        self._last_colour += 1
        return colour

    @property
    def colormap(self):
        backup_cmap = "viridis"
        try:
            cmap = self._unit_lookup._settings.group("colours").get("colormap")
        except:
            return backup_cmap
        else:
            if cmap in mpl.colormaps():
                return cmap
            else:
                return self._unit_lookup._settings.default_value("colours", "colormap")

    @Slot()
    def regenerate_colours(self):
        self._colour_list = get_mpl_colours()
        self._last_colour = 0
        for row in range(self.rowCount()):
            current_colour = self.item(row, plotting_column_index["Colour"]).text()
            if (
                current_colour
                != self._last_colour_list[row % len(self._last_colour_list)]
            ):
                LOG.debug(
                    f"colours not equal: {current_colour} vs {self._last_colour_list[row % len(self._last_colour_list)]}"
                )
                self._last_colour += 1
            else:
                next_colour = self.next_colour()
                self.item(row, plotting_column_index["Colour"]).setText(
                    str(next_colour)
                )
                self.item(row, plotting_column_index["Colour"]).setData(
                    QColor(str(next_colour)), role=Qt.ItemDataRole.BackgroundRole
                )
        self._last_colour_list = list(self._colour_list)

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
        factor, new_unit = self._unit_lookup.conversion_factor(unit)
        return new_unit

    def datasets(self) -> Dict:
        result = {}
        for ds_num, row in enumerate(range(self.rowCount())):
            key = self.index(row, plotting_column_index["Dataset"]).data(
                role=Qt.ItemDataRole.UserRole
            )
            useit = (
                self.itemFromIndex(
                    self.index(row, plotting_column_index["Use it?"])
                ).checkState()
                == Qt.CheckState.Checked
            )
            data_number_string = self.itemFromIndex(
                self.index(row, plotting_column_index["Use it?"])
            ).text()
            colour = self.itemFromIndex(
                self.index(row, plotting_column_index["Colour"])
            ).text()
            style = self.itemFromIndex(
                self.index(row, plotting_column_index["Line style"])
            ).text()
            marker = self.itemFromIndex(
                self.index(row, plotting_column_index["Marker"])
            ).text()
            axis = self.itemFromIndex(
                self.index(row, plotting_column_index["Main axis"])
            ).text()
            if useit:
                self._datasets[key].set_data_limits(data_number_string)
                result[key] = (self._datasets[key], colour, style, marker, ds_num, axis)
            else:
                self._datasets[key]._data_limits = None
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
                new_dataset.longest_axis()[-1],
                "",
                self.next_colour(),
                "-",
                "",
            ]
        ]
        for item in items:
            item.setData(newkey, role=Qt.ItemDataRole.UserRole)
        for item in items[:4]:
            item.setEditable(False)
        temp = items[plotting_column_index["Use it?"]]
        temp.setCheckable(True)
        temp.setCheckState(Qt.CheckState.Checked)
        self.itemChanged.connect(self.needs_an_update)
        temp = items[plotting_column_index["Colour"]]
        temp.setData(QColor(temp.text()), role=Qt.ItemDataRole.BackgroundRole)
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
        elif len(curves) == 1:
            LOG.debug("A single curve output from PlottingContext.")
        else:
            LOG.debug("No curves!")
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
        self.setHorizontalHeaderLabels(plotting_column_labels)
        return result

    @Slot(QModelIndex)
    def delete_dataset(self, index: QModelIndex):
        dkey = index.data(role=Qt.ItemDataRole.UserRole)
        self.removeRow(index.row())
        self._datasets.pop(dkey, None)
