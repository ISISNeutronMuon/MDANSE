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
import itertools
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import h5py

import matplotlib.pyplot as mpl
import numpy as np
from matplotlib import rcParams
from matplotlib.colors import to_hex as mpl_to_hex
from matplotlib.lines import lineStyles
from matplotlib.markers import MarkerStyle
from MDANSE.MLogging import LOG
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
import contextlib


def get_mpl_markers():
    """Return valid point markers provided by matplotlib."""
    unique_keys = list(set(MarkerStyle.markers.keys()))
    return {
        key: MarkerStyle.markers[key]
        for key in unique_keys
        if key not in ["", " ", "none"] + [str(x) for x in range(10)]
    }


def get_mpl_lines():
    """Return valid plot line styles used by matplotlib."""
    return {key: value for key, value in lineStyles.items() if key not in ["", " "]}


def get_mpl_colours():
    """Get matplotlib line colours from the current style, as hex string."""
    cycler = rcParams["axes.prop_cycle"]
    colours = cycler.by_key()["color"]
    return [mpl_to_hex(col) for col in colours]


class SingleDataset:
    """Manages a plottable data set from an .mda file."""

    def __init__(self, name: str, source: "h5py.File", linestyle: str = "-"):
        self._name = name
        self._filename = source.filename
        self._use_scaling = True
        self._curves = {}
        self._curve_labels = {}
        self._linestyle = linestyle
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
        self._scaling_factor = 1.0
        with contextlib.suppress(KeyError):
            try:
                self._scaling_factor = float(source[name].attrs["scaling_factor"])
            except TypeError:
                self._scaling_factor = np.array(source[name].attrs["scaling_factor"])
        self._axes = {}
        self._axes_units = {}
        self._axes_scaling = {}
        self._current_units = {}
        self._axes_order = []
        if self._axes_tag == "index":
            for dim_number, dim_length in enumerate(self._data.shape):
                temp_key = f"index{dim_number}"
                self._axes[temp_key] = np.arange(dim_length)
                self._axes_units[temp_key] = "N/A"
                self._current_units[temp_key] = "N/A"
                self._axes_scaling[temp_key] = 1.0
                self._axes_order.append(temp_key)
            return
        for ax_number, axis_name in enumerate(self._axes_tag.split("|")):
            aname = axis_name.strip()
            if aname == "index":
                axis_key = aname + str(ax_number)
                self._axes[axis_key] = np.arange(self._data.shape[ax_number])
                self._axes_units[axis_key] = "N/A"
            else:
                axis_key = aname
                self._axes[axis_key] = source[axis_key][:]
                self._axes_units[axis_key] = source[axis_key].attrs["units"]
            self._axes_order.append(axis_key)
            self._axes_scaling[axis_key] = 1.0
            self._current_units[axis_key] = self._axes_units[axis_key]

    def x_axis(self, axis_key: str) -> np.ndarray:
        """Get the plotting axis in the current physical units.

        Parameters
        ----------
        axis_key : str
            name of the axis associated with the data set.

        Returns
        -------
        np.ndarray
            An axis for plotting the dataset, after unit conversion

        """
        return self._axes[axis_key] * self._axes_scaling[axis_key]

    def x_axis_label(self, axis_key: str) -> str:
        """Get the axis label to be used as matplotlib label.

        Parameters
        ----------
        axis_key : str
            name of the axis dataset.

        Returns
        -------
        str
            Name of the dataset and the corresponding physical unit.

        """
        return f"{axis_key} ({self._current_units[axis_key]})"

    def set_current_units(self, unit_lookup):
        """Update the unit based on the unit lookup of the PlottingContext."""
        if unit_lookup is None:
            return
        for axis_name, axis_unit in self._axes_units.items():
            factor, new_unit = unit_lookup.conversion_factor(axis_unit)
            self._axes_scaling[axis_name] = factor
            self._current_units[axis_name] = new_unit

    def set_data_limits(self, limit_string: str):
        """Parse the string used for selecting a subset of data.

        Parameters
        ----------
        limit_string : str
            Data row indices, given as a list, range or slice.

        """
        complete_subset_list = []
        for token in limit_string.split(";"):
            if ":" in token:
                try:
                    slice_parts = [int(x) for x in token.split(":")]
                except Exception:
                    continue
                if len(slice_parts) < 4:
                    complete_subset_list += list(range(*slice_parts))
            elif "-" in token:
                try:
                    slice_parts = [int(x) for x in token.split("-")]
                except Exception:
                    continue
                if len(slice_parts) == 2:
                    complete_subset_list += list(range(slice_parts[0], slice_parts[1]))
            elif "," in token:
                try:
                    slice_parts = [int(x) for x in token.split(",")]
                except Exception:
                    continue
                complete_subset_list += list(slice_parts)
            else:
                try:
                    complete_subset_list += [int(token)]
                except Exception:
                    continue
        if len(complete_subset_list) == 0:
            self._data_limits = None
        else:
            self._data_limits = np.unique(complete_subset_list).astype(int)

    def available_x_axes(self) -> list[str]:
        """Get a list of axis names used by this data set.

        Returns
        -------
        list[str]
            Names of the axes used by this data set.

        """
        return list(self._axes_units.keys())

    def longest_axis(self) -> str:
        """Determine which axis is the longest, to be used as x axis.

        Returns
        -------
        str
            Name of the longest axis.

        """
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

    @property
    def data(self):
        """Data array, scaled if requested in the GUI table.

        Returns
        -------
        np.ndarray
            The plot data, scaled if set.

        """
        if self._use_scaling:
            return self._data * self._scaling_factor
        return self._data

    def generate_curve_label(
        self,
        index_tuple: tuple[int],
        axis_lookup: tuple[str],
    ) -> str:
        """Get a meaningful label for a subset of data.

        Used when plotting 1D arrays out of a multidimensional array.

        Parameters
        ----------
        index_tuple : tuple[int]
            indices of the 1D data array position in the ND array
        axis_lookup : tuple[str]
            Names of the axes to use

        Returns
        -------
        str
            A string label for the plot legend.

        """
        if self._n_dim < 2:
            return ""
        label = "at "
        for axis_index, axis_name in enumerate(axis_lookup):
            axis_values = self.x_axis(axis_name)
            axis_unit = self._current_units[axis_name]
            picked_value = axis_values[index_tuple[axis_index]]
            if len(axis_values) > 1:
                significant_digit = np.floor(
                    np.log10(abs(np.mean(axis_values[1:] - axis_values[:-1])))
                ).astype(int)
            elif len(axis_values) == 1:
                significant_digit = np.floor(np.log10(abs(axis_values[0]))).astype(int)
            else:
                label += f"{axis_name} has no values, unit {axis_unit}"
                continue
            if significant_digit < 0:
                picked_value = round(picked_value, abs(significant_digit) + 2)
            else:
                picked_value = round(picked_value, 1)
            label += f"{axis_name}={picked_value} {axis_unit}, "
        return label.rstrip(", ")

    def curves_vs_axis(
        self,
        x_axis_details: tuple[str],
        max_limit: int = 1,
    ) -> list[np.ndarray]:
        """Prepare a set of curves for plotting.

        Parameters
        ----------
        x_axis_details : tuple[str]
            Name and original unit of the primary plotting axis
        max_limit : int, optional
            Maximum number of curves allowed by plotter, by default 1

        Returns
        -------
        list[np.ndarray]
            List of data arrays ready for plotting

        """
        self._curves = {}
        self._curve_labels = {}
        current_dim = 0
        data_shape = self._data.shape
        x_axis_unit, x_axis_name = x_axis_details
        slicer = []
        indexer = []
        label_lookup = []
        axis_lengths = [len(self._axes[name]) for name in self._axes_order]
        if not np.allclose(data_shape, axis_lengths):
            raise ValueError("Array shape does not match the order of the axes")
        for axis_name in self._axes_order:
            axis_unit = self._axes_units[axis_name]
            if axis_unit == x_axis_unit and axis_name == x_axis_name:
                slicer.append([slice(None)])
            else:
                indices = np.arange(data_shape[current_dim])
                slicer.append(indices)
                indexer.append(indices)
                label_lookup.append(axis_name)
            current_dim += 1
        nd_indices = list(itertools.product(*indexer))
        slicers = list(itertools.product(*slicer))
        if self._data_limits is not None:
            curve_indices = self._data_limits
        else:
            curve_indices = range(max_limit)
        for counter, index in enumerate(curve_indices):
            if counter >= max_limit:
                break
            try:
                index_tuple = tuple(nd_indices[index])
                self._curves[index_tuple] = self.data[slicers[index]].squeeze()
                self._curve_labels[index_tuple] = self.generate_curve_label(
                    index_tuple,
                    label_lookup,
                )
            except IndexError:
                continue
        return self._curves

    def planes_vs_axis(self, axis_number: int, max_limit: int = 1) -> list[np.ndarray]:
        """Prepare for plotting 2D subsets of an ND array.

        Parameters
        ----------
        axis_number : int
            index of the axis perpendicular to the plotted array
        max_limit : int, optional
            maximum number of planes allowed by plotter, by default 1

        Returns
        -------
        list[np.ndarray]
            List of 2D arrays for heatmap plots

        """
        self._planes = {}
        self._plane_labels = {}
        _found = -1
        total_ndim = len(self._data.shape)
        if total_ndim == 1:
            return None
        if total_ndim == 2:
            return self.data
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
        if self._data_limits is not None:
            for counter, plane_number in enumerate(self._data_limits):
                if counter >= max_limit or plane_number >= number_of_planes:
                    break
                fixed_argument = perpendicular_axis[plane_number]
                slice_def[axis_number] = plane_number
                self._planes[plane_number] = self.data[tuple(slice_def)]
                self._plane_labels[plane_number] = (
                    f"{perpendicular_axis_name}={fixed_argument}"
                )
        else:
            for plane_number in range(max_limit):
                if plane_number >= number_of_planes:
                    break
                fixed_argument = perpendicular_axis[plane_number]
                slice_def[axis_number] = plane_number
                self._planes[plane_number] = self.data[tuple(slice_def)]
                self._plane_labels[plane_number] = (
                    f"{perpendicular_axis_name}={fixed_argument}"
                )
        return None


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
    "Apply weights?",
]
plotting_column_index = {
    label: number for number, label in enumerate(plotting_column_labels)
}


class PlottingContext(QStandardItemModel):
    """Data model storing data and user input used for plotting."""

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

    def generate_colour(self, number: int) -> str:
        """Get the matplotlib colour string for the nth curve.

        Parameters
        ----------
        number : int
            number of the curve in the plot

        Returns
        -------
        str
            colour string from the current matplotlib style

        """
        return self._colour_list[number % len(self._colour_list)]

    def next_colour(self) -> str:
        """Get the next matplotlib colour and increment the counter."""
        colour = self.generate_colour(self._last_colour)
        self._last_colour += 1
        return colour

    @property
    def colormap(self):
        """Matplotlib colormap out of the list of valid names."""
        backup_cmap = "viridis"
        try:
            cmap = self._unit_lookup._settings.group("colours").get("colormap")
        except Exception:
            return backup_cmap
        else:
            if cmap in mpl.colormaps():
                return cmap
            return self._unit_lookup._settings.default_value("colours", "colormap")

    @Slot()
    def regenerate_colours(self):
        """Populate the list of curve colours based on user input."""
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
                    str(next_colour),
                )
                self.item(row, plotting_column_index["Colour"]).setData(
                    QColor(str(next_colour)),
                    role=Qt.ItemDataRole.BackgroundRole,
                )
        self._last_colour_list = list(self._colour_list)

    @Slot(object)
    def accept_external_data(self, other: "PlottingContext"):
        """Copy the datasets from the input PlottingContext.

        Crucial slot for transferring data
        between tabs. DataPlotter will send the datasets
        into this slot.

        """
        for dataset in other._datasets.values():
            self.add_dataset(dataset)
        self.set_axes()

    @Slot(dict)
    def accept_units(self, units: dict):
        """Get user-preferred physical units from the input."""
        self._unit_preference = units
        self.set_axes()

    def get_conversion_factor(self, unit: str) -> str:
        """Find the output physical unit for the input unit.

        This lets us know what conversion will be performed.

        Parameters
        ----------
        unit : str
            physical unit of the original data set.

        Returns
        -------
        str
            physical unit after the conversion

        """
        _, new_unit = self._unit_lookup.conversion_factor(unit)
        return new_unit

    def datasets(self) -> dict:
        """Collect GUI inputs and return data sets for plotting.

        This method only returns data sets with "Use it" box checked.

        """
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
            set_scaling = (
                self.itemFromIndex(
                    self.index(row, plotting_column_index["Apply weights?"])
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
                self._datasets[key].set_current_units(self._unit_lookup)
                result[key] = (self._datasets[key], colour, style, marker, ds_num, axis)
            else:
                self._datasets[key]._data_limits = None
            self._datasets[key]._use_scaling = set_scaling

        return result

    def add_dataset(self, new_dataset: SingleDataset):
        """Add a SingleDataset instance to the model and GUI.

        Parameters
        ----------
        new_dataset : SingleDataset
            a SingleDataset instance

        """
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
                new_dataset._linestyle,
                "",
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
        temp = items[plotting_column_index["Apply weights?"]]
        temp.setEditable(False)
        temp.setCheckable(True)
        temp.setCheckState(Qt.CheckState.Checked)
        self.itemChanged.connect(self.needs_an_update)
        temp = items[plotting_column_index["Colour"]]
        temp.setData(QColor(temp.text()), role=Qt.ItemDataRole.BackgroundRole)
        self.appendRow(items)

    def set_axes(self):
        """Check that axis information can be found for datasets."""
        if len(self._datasets) == 0:
            return None
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
        """Remove all data from the model."""
        result = super().clear()
        self._datasets = {}
        self.setHorizontalHeaderLabels(plotting_column_labels)
        return result

    @Slot(QModelIndex)
    def delete_dataset(self, index: QModelIndex):
        """Delete a single row from the model."""
        dkey = index.data(role=Qt.ItemDataRole.UserRole)
        self.removeRow(index.row())
        self._datasets.pop(dkey, None)
