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

import copy
import functools
from collections.abc import Generator, Iterable, Sequence
from contextlib import suppress
from itertools import islice
from math import prod
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, overload

import h5py
import matplotlib.pyplot as mpl
import numpy as np
import numpy.typing as npt
from matplotlib import rcParams
from matplotlib.colors import to_hex as mpl_to_hex
from matplotlib.lines import lineStyles
from matplotlib.markers import MarkerStyle
from more_itertools import first, locate, nth, nth_product, sort_together, unzip
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel

from MDANSE.IO.IOUtils import summarise_array
from MDANSE.MLogging import LOG
from MDANSE.util_types import ComplexArray, FloatArray

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    import h5py

NUMBERS_FOR_SLICE = 3
NUMBERS_FOR_RANGE = 2
SCALE_FACTOR_FORMAT = "3.3f"


class PlotArgs(NamedTuple):
    """Arguments for plotting data."""

    dataset: SingleDataset
    colour: str
    line_style: str
    marker: str
    row: int
    main_axis: str
    legend_label: str


def get_mpl_markers():
    """Return valid point markers provided by matplotlib."""
    return {
        key: mark
        for key, mark in MarkerStyle.markers.items()
        if isinstance(key, str) and key not in {"", " ", "none"} and not key.isdigit()
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

    def __init__(
        self,
        name: str,
        source: h5py.File | None,
        linestyle: str = "-",
        marker: str | None = None,
        **kwargs,
    ):
        self._name = name
        self._use_scaling = True
        self._linestyle = linestyle
        self._marker = marker
        self._data_limits = None
        self._imaginary_data = None
        self._valid = True
        self._scaling_factor = 1.0
        self._main_axis = None
        self._axes: dict[str, FloatArray] = {}
        self._axes_units: dict[str, str] = {}
        self._current_units: dict[str, str] = {}
        self._axes_scaling: dict[str, float] = {}
        self._axes_order: list[str] = []
        self._xerror: FloatArray | None = None
        self._yerror: FloatArray | None = None

        self.configure(source, **kwargs)

    @functools.singledispatchmethod
    def configure(self, source: h5py.File | None, **kwargs) -> None:
        """Create plotting information depending on the input."""

    @configure.register
    def _(self, source: h5py.File) -> None:
        """Finish reading plotting axes from the input file.

        If you are setting data manually, use init_manually instead.

        Parameters
        ----------
        name : str
            Data set name in the file.
        source : h5py.File
            File object containing the data. A .mda HDF5 file.
        """
        self._filename = source.filename
        self.create_labels(self._filename)
        try:
            self._data = source[self._name][:]
        except KeyError:
            LOG.debug(f"{self._name} is not a data set in the file")
            self._valid = False
            return
        except TypeError:
            self._valid = False
            LOG.debug(f"{self._name} is not plottable")
            return

        temp_array = np.imag(self._data)
        if not np.allclose(temp_array, 0.0):
            self._imaginary_data = temp_array

        self._data = np.real(self._data)

        with suppress(KeyError):
            try:
                self._scaling_factor = float(source[self._name].attrs["scaling_factor"])
            except TypeError:
                self._scaling_factor = np.array(
                    source[self._name].attrs["scaling_factor"],
                )

        self._data_unit = source[self._name].attrs["units"]
        self._n_dim = len(self._data.shape)
        self._data_shape = self._data.shape
        self._axes_tag = source[self._name].attrs["axis"]

        self.create_axes_tags(self._axes_tag, source)

    @configure.register
    def _(
        self,
        _source: None,
        data: FloatArray,
        *,
        data_unit: str = "none",
        scaling_factor: float = 1.0,
        plot_axes: dict[str, FloatArray] | None = None,
        axes_units: dict[str, str] | None = None,
        yerror: FloatArray | None = None,
        xerror: FloatArray | None = None,
        optional_filename: str = "no file",
        uneven_array: bool = False,
    ) -> None:
        """Set data for plotting without using a data file.

        Makes it possible to create custom datasets for the MDANSE plotter.

        Parameters
        ----------
        data : FloatArray
            The data to be plotted. An N-dimensional array, N<=3
        data_unit : str, optional
            Physical unit of the values in the data array
        scaling_factor : float, optional
            Data will be scaled by this factor if requested, by default 1.0
        plot_axes : dict[str, FloatArray] | None, optional
            Dictionary of axis_name: axis_array pairs, by default None
        axes_units : dict[str, str] | None, optional
            Dictionary of axis_name: axis_unit pairs, by default None
        yerror: FloatArray | None = None
            Vertical error bars associated with the data points.
        xerror: FloatArray | None = None
            Horizontal error bars associated with the data points.
        optional_filename: str = "no file"
            File name to be displayed as the origin of this data set.
        uneven_array: bool = False
            If True, allow the data rows to be of different length.
        """
        self._filename = optional_filename
        self._labels = {
            "minimal": self._name,
            "medium": self._name,
            "full": self._name,
        }
        if uneven_array:
            self._data = data
            self._n_dim = 1
            self._data_shape = (len(data),)
            self._use_scaling = False
        else:
            self._data = np.real(data)
            self._n_dim = len(self._data.shape)
            self._data_shape = self._data.shape

        self._scaling_factor = scaling_factor
        self._xerror = xerror
        self._yerror = yerror

        self._data_unit = data_unit

        if plot_axes is None:
            for ax_number, npoints in enumerate(self._data.shape):
                axis_key = f"index{ax_number}"
                self._axes[axis_key] = np.arange(npoints)
                self._axes_units[axis_key] = "N/A"
                self._axes_order.append(axis_key)
                self._axes_scaling[axis_key] = 1.0
                self._current_units[axis_key] = self._axes_units[axis_key]
            self._axes_tag = "|".join(str(x) for x in self._axes)
            return

        for axis_key, axis_array in plot_axes.items():
            self._axes_tag = "|".join(str(x) for x in plot_axes)
            self._axes[axis_key] = axis_array
            self._axes_units[axis_key] = (
                "N/A" if axes_units is None else axes_units[axis_key]
            )
            self._axes_order.append(axis_key)
            self._axes_scaling[axis_key] = 1.0
            self._current_units[axis_key] = self._axes_units[axis_key]

    def create_axes_tags(self, axes_tag: str, source: h5py.File):
        """Find the right axes datasets for the current dataset.

        Parameters
        ----------
        axes_tag : str
            String form of the axis attribute of the main dataset
        source : h5py.File
            File object from which the axes datasets can be read.

        """
        if axes_tag == "index":
            for dim_number, dim_length in enumerate(self._data.shape):
                self._axes[f"index{dim_number}"] = np.arange(dim_length)
                self._axes_units[f"index{dim_number}"] = "N/A"
            return

        self._current_units = {}
        self._axes_scaling = {}
        self._axes_order = []

        for ax_number, axis_name in enumerate(axes_tag.split("|")):
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

    def x_axis(self, axis_key: str) -> FloatArray:
        """Get the plotting axis in the current physical units.

        Parameters
        ----------
        axis_key : str
            name of the axis associated with the data set.

        Returns
        -------
        FloatArray
            An axis for plotting the dataset, after unit conversion

        """
        return self._axes[axis_key] * self._axes_scaling[axis_key]

    @staticmethod
    def axis_true_name(axis_key: str) -> str:
        """Return the short name of the axis dataset without the path."""
        if "/" in axis_key:
            return axis_key.rsplit("/", 1)[1].strip()
        return axis_key

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
        return f"{self.axis_true_name(axis_key)} ({self._current_units[axis_key]})"

    def set_current_units(self, unit_lookup):
        """Update the unit based on the unit lookup of the PlottingContext."""
        if unit_lookup is None:
            return

        for axis_name, axis_unit in self._axes_units.items():
            factor, new_unit = unit_lookup.conversion_factor(axis_unit)
            self._axes_scaling[axis_name] = factor
            self._current_units[axis_name] = new_unit

    def create_labels(self, root_name: str):
        """Create several labels of different length for the plot legend.

        Parameters
        ----------
        root_name : str
            Path to the data file from which this data set has been read.

        """
        bare_name = Path(root_name).name
        self._labels = {
            "minimal": self._name,
            "medium": f"{bare_name}:{self._name}",
            "full": f"{root_name}:{self._name}",
        }

    def spawn_imaginary_dataset(self) -> SingleDataset | None:
        """Create another dataset with the imaginary part of the data.

        Returns
        -------
        SingleDataset | None
            None if data values are real, or SingleDataset of the imaginary part.

        """
        if self._imaginary_data is None:
            return None
        new_dataset = SingleDataset(f"{self._name}_imag", None)
        new_dataset._data = self._imaginary_data.copy()
        new_dataset.create_labels(self._filename)
        for attr in [
            "_axes",
            "_axes_units",
            "_axes_order",
            "_scaling_factor",
            "_data_unit",
            "_n_dim",
            "_filename",
        ]:
            setattr(new_dataset, attr, copy.deepcopy(getattr(self, attr)))
        return new_dataset

    @staticmethod
    def parse_token(token: str, max_len: int) -> Iterable[int]:
        """Parse a token component into an appropriate value for dimension slicing.

        Parameters
        ----------
        token : str
            Token to parse.
        max_len : int
            Size of array for un-ended slices.

        Returns
        -------
        Iterable[int]
            Parsed values.

        Examples
        --------
        >>> parse_token("3:5", 10)
        range(3, 5)
        >>> parse_token("3:60:2", 5)
        range(3, 5, 2)
        >>> parse_token("8", 10)
        (8, )
        >>> parse_token("6-8", 10)
        range(6, 8)
        """
        if ":" in token:
            slice_parts = map(int, token.split(":"))
            slc = slice(*slice_parts).indices(max_len)
            return range(*slc)

        if "-" in token:
            start, stop = map(int, token.split("-"))
            return range(start, stop + 1)

        return (int(token),)

    def set_data_limits(self, limit_string: str, main_axis: str = ""):
        """Parse the string used for selecting a subset of data.

        Parameters
        ----------
        limit_string : str
            Data row indices, given as a list, range or slice.

        """
        if not limit_string:
            self._data_limits = None
            return

        complete_subset: dict[int, None] = {}

        self._main_axis = main_axis
        axes = map(len, self.dep_axes.values())

        max_len = prod(axes)

        def add_ord(val: Iterable[int]) -> None:
            complete_subset.update(dict.fromkeys(val, None))

        for token in limit_string.split(";"):
            try:
                add_ord(self.parse_token(token, max_len))
            except Exception as err:
                LOG.error(
                    "Ignoring invalid token (%r) in set_data_limits.\n %s", token, err
                )
                continue

        self._data_limits = list(complete_subset)

    def available_x_axes(self) -> list[str]:
        """Get a list of axis names used by this data set.

        Returns
        -------
        list[str]
            Names of the axes used by this data set.

        """
        return list(self._axes_units.keys())

    def longest_axis(self) -> tuple[str, str]:
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
    def dep_axes(self) -> dict[str, FloatArray]:
        """Axes which are likely to be dependent."""
        la = self.longest_axis()[1] if not self._main_axis else self._main_axis
        return {aname: axis for aname, axis in self._axes.items() if aname != la}

    @property
    def data(self) -> npt.NDArray[np.floating]:
        """Data array, scaled if requested in the GUI table.

        Returns
        -------
        FloatArray
            The plot data, scaled if set.

        """
        if self._use_scaling:
            return self._data * self._scaling_factor
        return self._data

    @property
    def n_curves(self) -> int:
        """Number of curves in dataset."""
        if self._data_limits is None:
            return 0

        return len(self._data_limits)

    def generate_curve_label(
        self,
        index_tuple: Sequence[int],
        axis_lookup: Iterable[str],
        *,
        skip_text: bool = False,
    ) -> str:
        """Get a meaningful label for a subset of data.

        Used when plotting 1D arrays out of a multidimensional array.

        Parameters
        ----------
        index_tuple : Sequence[int]
            indices of the 1D data array position in the ND array.
        axis_lookup : Iterable[str]
            Names of the axes to use.
        skip_text : bool, optional
            If set to true, omits the text parts of the label. By default False.

        Returns
        -------
        str
            A string label for the plot legend or a number for Text plotter.

        """
        if self._n_dim < 2:
            return ""

        label = "at "

        for axis_index, axis_name in enumerate(axis_lookup):
            axis_label = self.axis_true_name(axis_name)

            axis_values = self.x_axis(axis_name)
            axis_unit = self._current_units[axis_name]
            picked_value = axis_values[index_tuple[axis_index]]

            if len(axis_values) > 1:
                data = np.mean(np.diff(axis_values))
            elif len(axis_values) == 1:
                data: np.floating = axis_values[0]
            else:
                label += f"{axis_label} has no values, unit {axis_unit}"
                continue

            significant_digit: np.integer = np.floor(np.log10(np.abs(data))).astype(int)

            if significant_digit < -20:
                picked_value = 0
            elif significant_digit < 0:
                picked_value = round(picked_value, abs(significant_digit) + 2)
            else:
                picked_value = round(picked_value, 1)

            label += f"{axis_label}={picked_value} {axis_unit}, "
            if skip_text:
                return str(float(picked_value))
        return label.rstrip(", ")

    def curve_ind(self, limits: int | None = None, /):
        """Get indices of valid axes.

        Parameters
        ----------
        limits : int
            Max number of curves to return.
        """
        return islice(self._data_limits, limits)

    def curves_vs_axis(
        self,
        axis_label: tuple[str, str] | str,
        max_limit: int | None = None,
        *,
        axis_unit: str | None = None,
        skip_label_text: bool = False,
    ) -> Generator[
        tuple[
            str | float | None,
            tuple[FloatArray, FloatArray],
        ]
    ]:
        """Prepare a set of curves for plotting.

        Parameters
        ----------
        axis_label : str
            Name of the primary plotting axis.
        axis_unit : str, optional
            Unit of the primary plotting axis.
        max_limit : int, optional
            Maximum number of curves allowed by plotter, by default 1
        skip_label_text: bool, optional
            Whether to skip the axis name and unit in the curve label, by default False.

        Yields
        ------
        str
            Plot label.
        npt.NDArray[np.floating]
            x-axis.
        npt.NDArray[np.floating]
            Curve to plot.
        """
        match axis_label:
            case (str(unit), str(label)):
                axis_unit = unit
                axis_label = label
            case str():
                pass
            case _:
                raise ValueError(f"Cannot handle {axis_label} as axis label")

        x_axis = self.x_axis(axis_label)

        if self._data.ndim == 1:
            yield axis_label, (x_axis, self.data)
            return

        data_shape = self._data.shape
        slicer = []
        indexer: list[Sequence[int]] = []
        label_lookup = []
        axis_lengths = [len(self._axes[name]) for name in self._axes_order]
        match_unit = axis_unit is not None

        if np.allclose(data_shape, axis_lengths):
            for current_dim, axis_name in enumerate(self._axes_order):
                curr_unit = self._axes_units[axis_name]

                if axis_name == axis_label and (
                    not match_unit or (axis_unit == curr_unit)
                ):
                    slicer.append([slice(None)])
                    continue

                indices: npt.NDArray[np.integer] = np.arange(data_shape[current_dim])
                slicer.append(indices)
                indexer.append(indices)
                label_lookup.append(axis_name)

            if not indexer:
                LOG.warning("Empty selection for data set %s", self._name)
                return

            for index in self.curve_ind(max_limit):
                try:
                    index_tuple = nth_product(index, *indexer)
                    index_slicer = nth_product(index, *slicer)

                    yield (
                        self.generate_curve_label(
                            index_tuple, label_lookup, skip_text=skip_label_text
                        ),
                        (x_axis, self.data[index_slicer].squeeze()),
                    )
                except IndexError:
                    LOG.warning(
                        "Skipping: in dataset %s, index %s is out of bounds",
                        self._name,
                        index,
                    )

        elif (
            len(axis_lengths) == 1
            and len(data_shape) == 2
            and data_shape[0] == axis_lengths[0]
        ):
            # Assume multiple lines in block

            axis_name = first(self._axes_order)

            for current_dim in range(data_shape[1]):
                yield (
                    axis_name,
                    (x_axis, self.data[:, current_dim]),
                )

        else:
            raise ValueError("Array shape does not match the order of the axes")

    def planes_vs_axis(
        self,
        axis_number: int,
        max_limit: int = 1,
    ) -> Generator[tuple[str, FloatArray]]:
        """Prepare for plotting 2D subsets of an ND array.

        Parameters
        ----------
        axis_number : int
            index of the axis perpendicular to the plotted array

        Yields
        ------
        str
            Grid label.
        npt.NDArray[np.floating]
            2D array.

        """
        match self._data.ndim:
            case 1:
                pass
            case 2 if axis_number == 1:
                yield self._labels["medium"], self.data.T
            case 2:
                yield self._labels["medium"], self.data
            case 3:
                perpendicular_axis_name, perpendicular_axis = nth(
                    self._axes.items(), axis_number, default=(None, None)
                )

                if perpendicular_axis is None:
                    return

                reordered_view = np.moveaxis(self.data, axis_number, 0)

                for plane_number in self.curve_ind(max_limit):
                    yield (
                        f"{self._labels['minimal']}:{perpendicular_axis_name}={perpendicular_axis[plane_number]}",
                        reordered_view[plane_number],
                    )
            case _:
                raise NotImplementedError(
                    f"Cannot handle {self._data.ndim}-dimensional data."
                )

    def main_axis_index(self, main_axis: str | None, *, default: int) -> int:
        """Find index of main axis.

        Parameters
        ----------
        main_axis : str
            Main axis name to search for.
        default : int
            Index if ``main_axis`` not found.

        Returns
        -------
        int
            Index of main axis.
        """
        return first(locate(self._axes, pred=lambda x: x == main_axis), default)


plotting_column_labels = [
    "Dataset",
    "Legend label",
    "Size",
    "Unit",
    "Main axis",
    "Use it?",
    "Colour",
    "Line style",
    "Marker",
    "Apply scaling?",
    "Trajectory",
]
plotting_column_index = {
    label: number for number, label in enumerate(plotting_column_labels)
}


class PlottingContext(QStandardItemModel):
    """Data model storing data and user input used for plotting."""

    needs_an_update = Signal("quint64")

    def __init__(
        self, *args, unit_lookup: int | None = None, colormap: str = "viridis", **kwargs
    ):
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
        self._colour_map = colormap
        self._last_colour = 0
        self._unit_lookup = unit_lookup
        self.plot_widget_id = -1
        self.use_legend = True
        self.use_grid = True
        self.setHorizontalHeaderLabels(plotting_column_labels)
        self.itemChanged.connect(self.ask_for_update)

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
                    f"colours not equal: {current_colour} vs "
                    f"{self._last_colour_list[row % len(self._last_colour_list)]}",
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
    def accept_external_data(self, other: PlottingContext):
        """Copy the datasets from the input PlottingContext.

        Crucial slot for transferring data
        between tabs. DataPlotter will send the datasets
        into this slot.

        """
        for dataset, plot_args in zip(
            other._datasets.values(), other.datasets().values(), strict=True
        ):
            self.add_dataset(dataset, optional_values=plot_args)
            self.add_dataset(
                dataset.spawn_imaginary_dataset(), optional_values=plot_args
            )
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

    def datasets(self) -> dict[str, PlotArgs]:
        """Collect GUI inputs and return data sets for plotting.

        This method only returns data sets with "Use it" box checked.

        """
        result = {}

        for row in range(self.rowCount()):
            row_data = {
                key: self.item(row, ind) for key, ind in plotting_column_index.items()
            }

            key = self.index(row, plotting_column_index["Dataset"]).data(
                role=Qt.ItemDataRole.UserRole,
            )
            useit = row_data["Use it?"].checkState() is Qt.CheckState.Checked
            self._datasets[key]._use_scaling = (
                row_data["Apply scaling?"].checkState() is Qt.CheckState.Checked
            )

            if not useit:
                self._datasets[key]._data_limits = None
                continue

            data_number_string = row_data["Use it?"].text()
            main_axis = row_data["Main axis"].text()

            self._datasets[key].set_data_limits(data_number_string, main_axis=main_axis)
            self._datasets[key].set_current_units(self._unit_lookup)
            result[key] = PlotArgs(
                dataset=self._datasets[key],
                colour=row_data["Colour"].text(),
                line_style=row_data["Line style"].text(),
                marker=row_data["Marker"].text(),
                row=row,
                main_axis=row_data["Main axis"].text(),
                legend_label=row_data["Legend label"].text(),
            )

        return result

    def add_dataset(
        self, new_dataset: SingleDataset, optional_values: PlotArgs | None = None
    ):
        """Add a SingleDataset instance to the model and GUI.

        Parameters
        ----------
        new_dataset : SingleDataset
            A SingleDataset instance.
        optional_values : PlotArgs | None
            If the dataset is being added from another model, the model.datasets() output can be added here.

        """
        if new_dataset is None or not new_dataset._valid:
            return

        newkey = f"{new_dataset._filename}:{new_dataset._name}"
        if newkey in self._datasets:
            return

        self._datasets[newkey] = new_dataset
        items = [
            QStandardItem(str(x))
            for x in (
                new_dataset._name,
                getattr(optional_values, "legend_label", new_dataset._labels["medium"]),
                new_dataset._data_shape,
                new_dataset._data_unit,
                new_dataset.longest_axis()[-1],
                "",
                self.next_colour(),
                new_dataset._linestyle,
                new_dataset._marker or "None",
                format(new_dataset._scaling_factor, SCALE_FACTOR_FORMAT)
                if isinstance(new_dataset._scaling_factor, float)
                else summarise_array(
                    new_dataset._scaling_factor, show=1, arr_fmt=SCALE_FACTOR_FORMAT
                ),
                new_dataset._filename,
            )
        ]

        fixed = {"Dataset", "Trajectory", "Size", "Unit", "Apply scaling?"}

        for key, item in zip(plotting_column_labels, items, strict=True):
            item.setData(newkey, role=Qt.ItemDataRole.UserRole)
            item.setEditable(key not in fixed)

        for key in ("Use it?", "Apply scaling?"):
            item = items[plotting_column_index[key]]
            item.setCheckable(True)
            item.setCheckState(
                Qt.CheckState.Checked
                if key == "Use it?" or new_dataset._use_scaling
                else Qt.CheckState.Unchecked,
            )

        items[plotting_column_index["Use it?"]].setText(
            f"0:{prod(len(arr) for arr in new_dataset.dep_axes.values())}:1",
        )

        temp = items[plotting_column_index["Colour"]]
        temp.setData(QColor(temp.text()), role=Qt.ItemDataRole.BackgroundRole)

        self.appendRow(items)
        self.add_dataset(new_dataset.spawn_imaginary_dataset())

    @Slot()
    def ask_for_update(self):
        """Emit a signal to indicate that a plot should be updated."""
        if self.plot_widget_id >= 0:
            self.needs_an_update.emit(self.plot_widget_id)

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

    def planes(
        self, default_axis: int = 0, planes_per_dataset: int | None = None
    ) -> Generator[tuple[PlotArgs, str, npt.NDArray[np.floating]]]:
        for databundle in self.datasets().values():
            ds = databundle.dataset

            for label, plane in islice(
                ds.planes_vs_axis(
                    ds.main_axis_index(databundle.main_axis, default=default_axis)
                ),
                planes_per_dataset,
            ):
                yield databundle, label, plane

    def curves(
        self, curves_per_dataset: int | None = None
    ) -> Generator[
        Generator[
            tuple[
                PlotArgs,
                str,
                tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]],
            ]
        ]
    ]:
        for databundle in self.datasets().values():
            ds = databundle.dataset

            yield (
                (databundle, label, curve)
                for label, curve in islice(
                    ds.curves_vs_axis(databundle.main_axis), curves_per_dataset
                )
            )
