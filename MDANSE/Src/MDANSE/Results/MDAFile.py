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
import sys
from collections.abc import Iterator, Mapping
from contextlib import suppress
from itertools import islice
from itertools import product as cart_prod
from math import prod
from pathlib import Path, PurePath
from textwrap import shorten
from types import TracebackType
from typing import TYPE_CHECKING, Any, Protocol, Self

import h5py
import numpy as np
from more_itertools import (
    argmax,
    collapse,
    first,
    locate,
    nth,
    nth_product,
    one,
    prepend,
    transpose,
)

from MDANSE.Core.Settings import Setting
from MDANSE.Framework.Formats.HDFFormat import check_metadata
from MDANSE.Framework.Units import Unit, measure
from MDANSE.IO.IOUtils import parse_index, summarise_array
from MDANSE.MLogging import LOG
from MDANSE.util_types import ComplexArray, FloatArray, IntArray

if sys.version_info < (3, 15):
    from types import MappingProxyType as frozendict

try:
    from matplotlib.pyplot import colormaps as mpl_colormaps
except ImportError:
    mpl_colormaps = ()

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Sequence

    class ProcessFunction(Protocol):
        def __call__(
            self,
            *,
            comment_character: str = "#",
            main_axis: str | None = None,
            units: Mapping[str, str | Unit | float] = frozendict({}),
        ) -> tuple[list[str], Iterator[Iterable[float]]]: ...


class MDAFile:
    """Representation of an MDA file."""

    def __init__(self, source: Path | str) -> None:
        self._file = h5py.File(source, "r")
        self._metadata = check_metadata(self._file)

        if self._metadata is None:
            self.close()
            raise ValueError(f"Not a .mda type file {source}")

        # Ensure only mda type file are loaded in Plot Creator Tab
        output_metadata = self._metadata["inputs/output_files"]

        if (
            not isinstance(output_metadata[1], list)
            or "MDAFormat" not in output_metadata[1]
        ):
            self.close()
            raise ValueError(f"Not a .mda type file {source}")

        self.all_children = list[PurePath]()
        self._file.visititems(self._get_ds)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_value: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def __del__(self) -> None:
        if getattr(self, "_file", None) is not None:
            self.close()

    def items(self, *, main: bool = True) -> Generator[tuple[str, SingleDataset]]:
        if main:
            yield from zip(
                map(str, self.main_dataset_paths), self.main_datasets, strict=True
            )
            return

        yield from zip(map(str, self.all_dataset_paths), self.all_datasets, strict=True)

    def as_dict(self, *, main: bool = True) -> dict[str, SingleDataset]:
        return dict(self.items(main=main))

    def close(self) -> None:
        """Close the HDF5 file."""
        self._file.close()

    def __getitem__(self, key: str) -> SingleDataset:
        keys = self.find_paths(key)
        found = one(
            keys,
            too_long=KeyError(
                f"Multiple matching keys for {key} ({', '.join(map(str, keys))})"
            ),
            too_short=KeyError(f"Key ({key}) not found"),
        )
        return SingleDataset(str(found), self._file)

    def __contains__(self, key: str) -> bool:
        return any(p.match(key) for p in self.all_dataset_paths)

    @property
    def filename(self) -> str:
        """Backing filename."""
        return self._file.filename

    @property
    def all_dataset_paths(self) -> Generator[PurePath]:
        """Paths to all datasets."""
        yield from (p for p in self.all_children if not p.is_relative_to("metadata"))

    @property
    def all_raw_datasets(self) -> Generator[h5py.Dataset]:
        """All datasets as read from HDF."""
        for pth in self.all_dataset_paths:
            yield self._file[str(pth)]

    @property
    def all_datasets(self) -> Generator[SingleDataset]:
        """All datasets as :class:`SingleDataset` s."""
        for pth in self.all_dataset_paths:
            tags = self._get_tags(pth)
            yield SingleDataset(
                str(pth), self._file, linestyle="-" if "main" in tags else "--"
            )

    @property
    def main_dataset_paths(self) -> Generator[PurePath]:
        """Paths to main datasets."""
        yield from filter(self._is_main, self.all_children)

    @property
    def main_raw_datasets(self) -> Generator[h5py.Dataset]:
        """Main datasets as read from HDF."""
        for pth in self.main_dataset_paths:
            yield self._file[str(pth)]

    @property
    def main_datasets(self) -> Generator[SingleDataset]:
        """Main datasets as :class:`SingleDataset` s."""
        for pth in self.main_dataset_paths:
            tags = self._get_tags(pth)
            yield SingleDataset(
                str(pth), self._file, linestyle="--" if "partial" in tags else "-"
            )

    def find_paths(self, key: str) -> list[PurePath]:
        """Find all paths matching key."""
        return [pth for pth in self.all_dataset_paths if pth.match(key)]

    def find_raw_datasets(self, key: str) -> list[h5py.Dataset]:
        """Find all raw datasets matching key."""
        return [self._file[str(pth)] for pth in self.find_paths(key)]

    def find_datasets(self, key: str) -> list[SingleDataset]:
        """Find all datasets matching key as :class:`SingleDataset`."""
        return [SingleDataset(str(pth), self._file) for pth in self.find_paths(key)]

    def _get_ds(self, name: str, obj: h5py.Group | h5py.Dataset) -> None:
        if isinstance(obj, h5py.Dataset):
            self.all_children.append(PurePath(name))

    def _get_tags(self, pth: PurePath | str) -> Mapping[str, Any]:
        return self._file[str(pth)].attrs

    def _is_main(self, pth: PurePath | str) -> bool:
        return (tags := self._get_tags(pth).get("tags", [])) and "main" in tags

    def summary(self, *, verbose: bool = False, width: int = 80) -> str:
        text = str(self.filename) + "\n"
        text += "===HEADER===\n"

        attrs = self._file.attrs
        if verbose:
            text += "\n".join(f"{key}: {attrs[key]}\n" for key in attrs)

        else:
            for attr in attrs:
                text += f"{attr}\n"
                for line in attrs[attr].splitlines():
                    if "=" in line:
                        text += shorten(line, width, placeholder="...") + "\n"
        text += "===DATASETS===\n"
        for pth, ds in zip(self.all_dataset_paths, self.all_raw_datasets, strict=True):
            text += f"{pth}: type={ds.dtype}, shape={ds.shape}\n"
        if not verbose:
            text += "\n The header output was truncated. Use verbose for full output\n"
        return text


class SingleDataset:
    """Manages a plottable data set from an .mda file."""

    colour_map = Setting(
        "viridis",
        group="matplotlib",
        comment="Name of the default matplotlib colormap to be used in 2D plots.",
    )

    def __init__(
        self,
        name: str,
        source: h5py.File | None,
        linestyle: str = "-",
        marker: str | None = None,
        colour_map: str = "",
        **kwargs,
    ):
        self._name = name
        self._use_scaling = True
        self._linestyle = linestyle
        self._marker = marker

        self._colour_map = colour_map or self.colour_map

        if mpl_colormaps and self._colour_map not in mpl_colormaps:
            LOG.error(
                "Colourmap (%s) not in permitted colourmaps, defaulting to 'viridis'. \nSupported: %s",
                self._colour_map,
                ", ".join(mpl_colormaps),
            )
            self._colour_map = "viridis"
            if self.colour_map not in mpl_colormaps:
                self.colour_map = "viridis"

        self._data_limits = None
        self._imaginary_data = None
        self._valid = True
        self._scaling_factor = 1.0
        self._axes: dict[str, FloatArray] = {}
        self._axes_units: dict[str, str] = {}
        self._current_units: dict[str, str] = {}
        self._axes_scaling: dict[str, float] = {}
        self._axes_order: list[str] = []
        self._xerror: FloatArray | None = None
        self._yerror: FloatArray | None = None

        self.configure(source, **kwargs)
        _, self._main_axis = self.longest_axis()
        self.set_data_limits(":", self._main_axis)

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
            data: ComplexArray | FloatArray = source[self._name][:]
        except KeyError:
            LOG.debug(f"{self._name} is not a dataset in the file")
            self._valid = False
            return
        except TypeError:
            LOG.debug(f"{self._name} is not plottable")
            self._valid = False
            return

        temp_array = np.imag(data)
        if not np.allclose(temp_array, 0.0):
            self._imaginary_data = temp_array

        self._data = np.real(data)

        with suppress(KeyError):
            try:
                self._scaling_factor = float(source[self._name].attrs["scaling_factor"])
            except TypeError:
                self._scaling_factor = np.array(
                    source[self._name].attrs["scaling_factor"],
                )

        self._data_unit = source[self._name].attrs["units"]
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
        data : FloatArray | None, optional
            The data to be plotted. An N-dimensional array, N<=3, by default None
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
            self._use_scaling = False
        else:
            self._data = np.real(data)

        self._scaling_factor = scaling_factor
        self._xerror = xerror
        self._yerror = yerror

        self._data_unit = data_unit

        if plot_axes is None:
            for ax_number, npoints in enumerate(self.shape):
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

    def summary(
        self,
        *,
        rows: int | None = None,
        cols: int | None = None,
        separator: str = ",",
        fmt: str | None = None,
    ) -> str:
        """Display summary of dataset.

        Parameters
        ----------
        rows : int, optional
            Rows of data to display (all if ``None``).
        cols : int, optional
            Columns of data to display (all if ``None``).
        separator : str
            Separator to use.
        fmt : str, optional
            Format for data in table.

        Returns
        -------
        str
            Text summary.
        """
        return (
            "\n".join(self.make_dataset_header())
            + "\n"
            + summarise_array(
                self._data, rows=rows, cols=cols, separator=separator, arr_fmt=fmt
            )
        )

    def create_axes_tags(self, axes_tag: str, source: h5py.File) -> None:
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
        return self._axes[axis_key] * self._axes_scaling.get(axis_key, 1.0)

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

    def set_current_units(self, unit_lookup) -> None:
        """Update the unit based on the unit lookup."""
        if unit_lookup is None:
            return

        for axis_name, axis_unit in self._axes_units.items():
            factor, new_unit = unit_lookup.conversion_factor(axis_unit)
            self._axes_scaling[axis_name] = factor
            self._current_units[axis_name] = new_unit

    def create_labels(self, root_name: str) -> None:
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
        new_dataset = SingleDataset(
            f"{self._name}_imag", None, data=self._imaginary_data.copy()
        )
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

    def set_data_limits(self, limit_string: str, main_axis: str = "") -> None:
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
                add_ord(parse_index(token, max_len))
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
            Name of axis unit.
        str
            Name of the longest axis.
        """
        if not self._axes_units:
            return ("none", "none")

        n = argmax(self._axes_units.values(), key=len)
        best_axis, best_unit = nth(
            self._axes_units.items(), n, default=("none", "none")
        )
        return best_unit, best_axis

    @property
    def dep_axes(self) -> dict[str, FloatArray]:
        """Axes which are likely to be dependent."""
        la = self.longest_axis()[1] if not self._main_axis else self._main_axis
        return {aname: axis for aname, axis in self._axes.items() if aname != la}

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of underlying data."""
        return self._data.shape

    @property
    def n_dims(self) -> int:
        """Number of dimensions in underlying data."""
        return self._data.ndim

    @property
    def data(self) -> FloatArray:
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
        if self.n_dims < 2:
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

    def curve_ind(self, limits: int | None = None, /) -> islice[int]:
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
        FloatArray
            x-axis.
        FloatArray
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
            yield "", (x_axis, self.data)
            return

        data_shape = self._data.shape
        slicer = []
        indexer: list[Sequence[int]] = []
        label_lookup = []
        axis_lengths = [len(self._axes[name]) for name in self._axes_order]
        match_unit = axis_unit is not None

        if (
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

        elif np.allclose(data_shape, axis_lengths):
            for current_dim, axis_name in enumerate(self._axes_order):
                curr_unit = self._axes_units[axis_name]

                if axis_name == axis_label and (
                    not match_unit or (axis_unit == curr_unit)
                ):
                    slicer.append([slice(None)])
                    continue

                indices: IntArray = np.arange(data_shape[current_dim])
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

        else:
            raise ValueError("Array shape does not match the order of the axes")

    def planes_vs_axis(
        self,
        main_axis: str,
        max_limit: int = 9,
    ) -> Generator[tuple[str, FloatArray, tuple[str, str]]]:
        """Prepare for plotting 2D subsets of an ND array.

        Parameters
        ----------
        main_axis : str
            Label of the axis perpendicular to the plotted array.

        Yields
        ------
        main_label : str
            Grid label.
        image_array : FloatArray
            2D array.
        axis_labels : tuple[str, ...]
            Labels for each axis.
        """
        main_axis_index = self.main_axis_index(main_axis)
        other_labels = self._axis_labels(main_axis)

        match self.n_dims:
            case 1:
                pass
            case 2 if main_axis_index == 1:
                yield self._labels["medium"], self.data.T, (main_axis, other_labels[0])
            case 2:
                yield self._labels["medium"], self.data, (main_axis, other_labels[0])
            case 3:
                perpendicular_axis_name, perpendicular_axis = nth(
                    self._axes.items(), main_axis_index, default=(None, None)
                )

                if perpendicular_axis is None:
                    return

                perpendicular_axis = self.x_axis(perpendicular_axis_name)

                reordered_view = np.moveaxis(self.data, main_axis_index, 0)

                for plane_number in self.curve_ind(max_limit):
                    if plane_number > len(reordered_view):
                        continue

                    yield (
                        f"{self._labels['minimal']}:{perpendicular_axis_name} = {perpendicular_axis[plane_number]:.5g} ({self._current_units[main_axis]})",
                        reordered_view[plane_number],
                        other_labels,
                    )
            case _:
                raise NotImplementedError(
                    f"Cannot handle {self._data.ndim}-dimensional data."
                )

    def main_axis_index(
        self, main_axis: str | None, *, default: int | None = None
    ) -> int:
        """Find index of main axis.

        Parameters
        ----------
        main_axis : str
            Main axis name to search for.
        default : int, optional
            Index if ``main_axis`` not found.

        Returns
        -------
        int
            Index of main axis.

        Raises
        ------
        ValueError
            Axis not found and no default.
        """
        ind = first(locate(self._axes, pred=main_axis.__eq__), default)
        if ind is None:
            raise ValueError(
                f"Cannot find axis {main_axis} in {','.join(self._axes.keys())}"
            )
        return ind

    def _axis_labels(self, main_axis: str) -> tuple[str] | tuple[str, str]:
        main_axis_index = self.main_axis_index(main_axis)

        return tuple(
            label for i, label in enumerate(self._axes) if i != main_axis_index
        )

    @property
    def processors(self) -> frozendict[int, ProcessFunction]:
        return frozendict(
            {
                1: self._as_1D_table,
                2: self._as_2D_table,
            }
        )

    def as_table(
        self,
        *,
        comment_character: str = "#",
        main_axis: str | None = None,
        units: Mapping[str, str | Unit | float] | None = frozendict({}),
    ) -> tuple[list[str], Iterator[Iterable[float]]]:
        """Wrapper for appropriately handling ND data."""
        if units is None:
            units = frozendict({})

        return self.processors.get(self.n_dims, self._as_ND_table)(
            main_axis=main_axis, comment_character=comment_character, units=units
        )

    def make_dataset_header(self, comment_character: str = "#") -> list[str]:
        """Return the dataset informartion as text.

        Extracts information related to the input dataset, and converts them
        into text. Returns a list of strings.

        Parameters
        ----------
        dataset : SingleDataset
            A dataset from MDANSE analysis results.
        comment_character : str, optional
            character used as prefix of the text header, by default '#'

        Returns
        -------
        list[str]
            list of header lines

        """
        lines = [
            f"{comment_character} Dataset name: {self._name}",
            f"{comment_character} from file {self._filename}",
            f"{comment_character} Contains axes: "
            + ", ".join(map(str, self.available_x_axes())),
            f"{comment_character} data unit is {self._data_unit}",
        ]
        return lines

    @staticmethod
    def _get_unit(from_unit: str, unit: float | Unit | str) -> float:
        """Get conversion factor for given unit."""
        match unit:
            case float() | int():
                conversion_factor = unit
            case Unit():
                conversion_factor = measure(1.0, from_unit, equivalent=True).toval(
                    unit._uname
                )
            case str():
                conversion_factor = measure(1.0, from_unit, equivalent=True).toval(unit)
            case _:
                conversion_factor = 1.0

        return conversion_factor

    def _as_1D_table(
        self,
        *,
        comment_character="#",
        units: Mapping[str, str | Unit | float] = frozendict({}),
        main_axis: str | None = None,
    ) -> tuple[list[str], Iterator[Iterable[float]]]:
        """Turn a 1D array into text.

        Formats a 1D array as a 2-column table with a commented header.
        The first column is determined using the information stored
        in the PlottingContext.

        Parameters
        ----------
        dataset : PlotArgs
            A SingleDataset with the GUI parameters.

        Returns
        -------
        list[str]
            Header lines.
        Iterator[Iterable[float]]
            A data table with 2 columns.

        """
        header_lines = self.make_dataset_header(comment_character=comment_character)
        best_unit, best_axis = self.longest_axis()
        xaxis_unit = units.get(best_axis, best_unit)

        conversion_factor = self._get_unit(best_unit, xaxis_unit)

        header_lines.append(f"{comment_character} units of x axis here: {xaxis_unit}")
        header_lines.append(
            f"{comment_character} col1:{best_axis}:{xaxis_unit} col2:data:{self._data_unit}"
        )

        return header_lines, zip(
            self._axes[best_axis] * conversion_factor, self.data, strict=True
        )

    def _as_2D_table(
        self,
        *,
        comment_character="#",
        main_axis: str | None = None,
        units: Mapping[str, str | Unit | float] = frozendict({}),
    ) -> tuple[list[str], Iterator[Iterable[float]]]:
        """Convert a 2D data array into text.

        Parameters
        ----------
        dataset : PlotArgs
            A SingleDataset with the GUI parameters.
        main_axis : str or None
            Main axis to plot.

        Returns
        -------
        list[str]
            Header lines.
        2D Iterator or Iterators
            A data table

            0. Axes->
            A  0,0 1,0 2,0 3,0 ...
            x  0,1 ⋱   2,1 3,1 ...
            e  0,2   ⋱
            s  0,3 1,3 ...
            |  ⋮
            v

        """
        header_lines = self.make_dataset_header(comment_character)

        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}

        flip_array = main_axis is not None and main_axis in self.available_x_axes()[1:]

        for n, ax_key in enumerate(self.available_x_axes()):
            axis = self._axes[ax_key]
            axis_unit = self._axes_units[ax_key]

            new_unit = units.get(ax_key, axis_unit)
            conv_factor = self._get_unit(axis_unit, new_unit)

            new_axes[ax_key] = axis * conv_factor
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key

            LOG.debug(f"process_2D_data: axis {ax_key} has length {len(axis)}")

            rc = "column" if n else "row"
            header_lines.append(
                f"{comment_character} first {rc} is {ax_key} in units {new_unit}"
            )

        LOG.debug(f"Data shape: {self._data.shape}")
        try:
            best_unit, best_axis = (
                self._axes_units[main_axis],
                main_axis,
            )
        except KeyError:
            best_unit, best_axis = self.longest_axis()

        curves_limit = self._data.shape[0] if flip_array else self._data.shape[1]

        # Add corner nil
        xaxis = prepend("_", new_axes[axis_numbers[flip_array]].flat)

        # Add axes to data
        data_lines = (
            (x[0], x[1][1])
            for x in self.curves_vs_axis(
                (best_unit, best_axis), max_limit=curves_limit, skip_label_text=True
            )
        )

        # Put xaxis in
        temp = prepend(xaxis, data_lines)

        # Flatten each row
        temp = map(collapse, temp)

        if flip_array:
            return header_lines, transpose(temp)

        return header_lines, temp

    def _as_ND_table(
        self,
        *,
        comment_character="#",
        units: Mapping[str, str | Unit | float] = frozendict({}),
        main_axis: str | None = None,
    ) -> tuple[list[str], Iterator[Iterable[float]]]:
        """Convert an N-dimensional data array into text.

        Parameters
        ----------
        dataset : PlotArgs
            A SingleDataset with the GUI parameters.
        main_axis : str or None
            Main axis to plot.

        Returns
        -------
        list[str]
            Header lines.
        Iterator[Iterable[float]]
            Data table of x,y,z,... data

        """

        header_lines = self.make_dataset_header(comment_character)
        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}

        for n, ax_key in enumerate(self.available_x_axes()):
            axis_unit = self._axes_units[ax_key]
            new_unit = units.get(ax_key, axis_unit)
            conv_factor = self._get_unit(axis_unit, new_unit)

            axis = self._axes[ax_key]
            new_axes[ax_key] = conv_factor * axis
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key
            LOG.debug("process_ND_data: axis %s has length %d.", ax_key, len(axis))

        for ax_num, ax_key in enumerate(new_axes):
            header_lines.append(
                f"{comment_character} {ax_num} column is {ax_key} in units {new_axes_units[ax_key]}"
            )

        LOG.debug(f"Data shape: {self._data.shape}")

        ax_lengths = [len(new_axes[ax_num]) for ax_num in axis_numbers.values()]
        LOG.debug(f"Axis lengths: {ax_lengths}")
        LOG.debug(f"Axis sequence: {axis_numbers}")

        # Attach axis indices
        temp = zip(
            cart_prod(*(new_axes[ind] for ind in axis_numbers.values())),
            self.data.ravel(),
            strict=True,
        )
        # Flatten each row
        temp = map(collapse, temp)

        return header_lines, temp

    def __repr__(self) -> str:
        return f"SingleDataset({self._name!r}, {self._filename!r})"
