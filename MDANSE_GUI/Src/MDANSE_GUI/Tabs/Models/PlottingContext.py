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

from itertools import islice
from math import prod
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
from matplotlib import rcParams
from matplotlib.colors import to_hex as mpl_to_hex
from matplotlib.colors import to_rgb
from matplotlib.lines import lineStyles
from matplotlib.markers import MarkerStyle
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel

from MDANSE.IO.IOUtils import summarise_array
from MDANSE.MLogging import LOG
from MDANSE.Results.MDAFile import SingleDataset
from MDANSE.util_types import FloatArray

if TYPE_CHECKING:
    from collections.abc import Generator


NUMBERS_FOR_SLICE = 3
NUMBERS_FOR_RANGE = 2
SCALE_FACTOR_FORMAT = "3.3f"


class PlotArgs(NamedTuple):
    """Arguments for plotting data."""

    dataset: SingleDataset
    colour_1: str
    colour_2: str
    colour_map: str
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


plotting_column_labels = [
    "Dataset",
    "Legend label",
    "Size",
    "Unit",
    "Main axis",
    "Use it?",
    "Colour 1",
    "Colour 2",
    "Colour map",
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

    def __init__(self, *args, unit_lookup: int | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._datasets: dict[str, SingleDataset] = {}
        self._current_axis = [None, None, None]
        self._figure = None
        self._ndim_lowest = 1
        self._ndim_highest = 3
        self._all_xunits = []
        self._best_xunits = []
        self._unit_preference = {}
        self._colour_list = get_mpl_colours()
        self._last_colour_list = get_mpl_colours()
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

    def next_colour(self) -> tuple[str, str]:
        """Get the next matplotlib colour and increment the counter."""
        colour = self.generate_colour(self._last_colour)
        r, g, b = to_rgb(colour)
        self._last_colour += 1
        return colour, mpl_to_hex((1 - r, 1 - g, 1 - b))

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
                next_colour, inverted = self.next_colour()
                self.item(row, plotting_column_index["Colour 1"]).setText(
                    str(next_colour),
                )
                self.item(row, plotting_column_index["Colour 1"]).setData(
                    QColor(str(next_colour)),
                    role=Qt.ItemDataRole.BackgroundRole,
                )
                self.item(row, plotting_column_index["Colour 2"]).setText(
                    str(inverted),
                )
                self.item(row, plotting_column_index["Colour 2"]).setData(
                    QColor(str(inverted)),
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
                key: dat
                for key, ind in plotting_column_index.items()
                if (dat := self.item(row, ind)) is not None
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
                colour_1=row_data["Colour 1"].text(),
                colour_2=row_data["Colour 2"].text(),
                colour_map=row_data["Colour map"].text(),
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
        next_colour, inverted = self.next_colour()
        items = [
            QStandardItem(str(x))
            for x in (
                new_dataset._name,
                getattr(optional_values, "legend_label", new_dataset._labels["medium"]),
                new_dataset.shape,
                new_dataset._data_unit,
                new_dataset.longest_axis()[-1],
                "",
                next_colour,
                inverted,
                new_dataset._colour_map,
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

        temp = items[plotting_column_index["Colour 1"]]
        temp.setData(QColor(temp.text()), role=Qt.ItemDataRole.BackgroundRole)
        temp = items[plotting_column_index["Colour 2"]]
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
            n_dimensions = dataset.n_dims
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
        self, default_axis: int | None = None, planes_per_dataset: int | None = None
    ) -> Generator[tuple[PlotArgs, str, FloatArray, tuple[str, str]]]:
        for databundle in self.datasets().values():
            ds = databundle.dataset

            for label, plane, axis_labels in islice(
                ds.planes_vs_axis(databundle.main_axis),
                planes_per_dataset,
            ):
                yield databundle, label, plane, axis_labels

    def curves(
        self, curves_per_dataset: int | None = None
    ) -> Generator[
        Generator[
            tuple[
                PlotArgs,
                str,
                tuple[FloatArray, FloatArray],
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
