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

from collections.abc import Iterator
from functools import reduce
from itertools import islice
from itertools import product as cart_prod
from math import prod as product
from typing import TYPE_CHECKING

import numpy as np
from more_itertools import collapse, prepend, transpose

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QTextBrowser

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset


class DatasetFormatter:
    """Converts a plotting dataset into text.

    Independent of the GUI component, DatasetFormatter
    takes a PlottingContext and converts each of its
    datasets into text.
    The text can then be displayed by the plotter,
    outside of this class.
    """

    def __init__(self):
        self._plotting_context = None
        self._new_header = "# MDANSE Data \n"
        self._new_text = []
        self._is_preview = True
        self._preview_lines = 10
        self._preview_columns = 10
        self._rounding_prec = 5
        self._comment = "#"
        self._separator = " "

    def take_new_input(self, pc: PlottingContext):
        """Assign the input PlottingContext to the plotter.

        The plotting context is passed from the GUI and
        contains datasets that have been selected by the user.
        This method converts each one of them to text and
        makes the result available to any GUI widget that
        may be used to display it.

        Parameters
        ----------
        pc : PlottingContext
            Data model containing the datasets for plotting

        Returns
        -------
        list[str]
            A list of (multi-line) text strings, one per dataset

        """
        self._plotting_context = pc
        self._new_text = []

        if self._plotting_context is None:
            return ["No data selected"]

        for databundle in self._plotting_context.datasets().values():
            header, data = self.process_data(
                databundle.dataset,
                main_axis=databundle.main_axis,
            )
            self._new_text.append(
                self.join_for_gui(header, data, separator=self._separator)
            )

        return self._new_text

    def datasets_for_csv(self):
        """Return the datasets to be saved in a text file."""
        if self._plotting_context is None:
            return ["No data selected"]

        for databundle in self._plotting_context.datasets().values():
            yield self.process_data(databundle.dataset, separator=self._separator)

    def make_dataset_header(self, dataset: SingleDataset, comment_character="#"):
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
            f"{comment_character} Dataset name: {dataset._name}",
            f"{comment_character} from file {dataset._filename}",
            f"{comment_character} Contains axes: "
            + ", ".join(map(str, dataset.available_x_axes())),
            f"{comment_character} data unit is {dataset._data_unit}",
        ]
        return lines, comment_character

    def join_for_gui(
        self,
        header_lines: list[str],
        data_array: Iterator[Iterator[float]],
        separator: str = " ",
    ):
        """Combine the header text with the data array into a string."""
        if self._is_preview:
            data = islice(data_array, self._preview_lines)
            data = map(lambda x: islice(x, self._preview_columns), data)
        else:
            data = data_array

        text_data = "\n".join(
            separator.join(str(round(x, self._rounding_prec)) for x in line)
            for line in data
        )

        # If not empty
        if self._is_preview and next(data_array, None) is not None:
            text_data += "\n..."

        new_header = "\n".join(header_lines)
        return new_header + "\n" + text_data

    def process_data(
        self,
        dataset: SingleDataset,
        main_axis: str | None = None,
    ):
        """Wrapper for approriately handling ND data."""

        if dataset._n_dim == 1:
            return self.process_1D_data(dataset)
        if dataset._n_dim == 2:
            return self.process_2D_data(dataset, main_axis=main_axis)

        return self.process_ND_data(dataset)

    def process_1D_data(
        self,
        dataset: SingleDataset,
    ) -> tuple[list[str], Iterator[Iterator[float]]]:
        """Turn a 1D array into text.

        Formats a 1D array as a 2-column table with a commented header.
        The first column is determined using the information stored
        in the PlottingContext.

        Parameters
        ----------
        dataset : SingleDataset
            A SingleDataset read from an .MDA file (HDF5).
        separator : str, optional
            Character(s) separating numbers in the output table, by default " ".

        Returns
        -------
        list[str]
            Header lines.
        np.ndarray
            A data table with 2 columns.

        """
        header_lines, _ = self.make_dataset_header(
            dataset, comment_character=self._comment
        )
        best_unit, best_axis = dataset.longest_axis()
        xaxis_unit = self._plotting_context.get_conversion_factor(best_unit)

        try:
            conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                xaxis_unit
            )
        except Exception:
            conversion_factor = 1.0
            # return f"Could not convert {best_unit} to {xaxis_unit}."

        header_lines.append(f"{self._comment} units of x axis here: {xaxis_unit}")
        header_lines.append(
            f"{self._comment} col1:{best_axis}:{xaxis_unit} col2:data:{dataset._data_unit}"
        )

        return header_lines, zip(
            dataset._axes[best_axis] * conversion_factor, dataset.data
        )

    def process_2D_data(
        self,
        dataset: SingleDataset,
        *,
        main_axis: str | None = None,
    ) -> tuple[list[str], Iterator[Iterator[float]]]:
        """Convert a 2D data array into text.

        Parameters
        ----------
        dataset : SingleDataset
            A SingleDataset read from an .MDA file (HDF5).
        separator : str, optional
            Character(s) separating numbers in the output table, by default " ".
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
        header_lines, comment_char = self.make_dataset_header(
            dataset, comment_character=self._comment
        )

        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}

        flip_array = (
            main_axis is not None and main_axis in dataset.available_x_axes()[1:]
        )

        for n, ax_key in enumerate(dataset.available_x_axes()):
            axis = dataset._axes[ax_key]
            axis_unit = dataset._axes_units[ax_key]
            new_unit = self._plotting_context.get_conversion_factor(axis_unit)
            conv_factor = measure(1.0, axis_unit, equivalent=True).toval(new_unit)

            new_axes[ax_key] = axis * conv_factor
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key

            LOG.debug(f"process_2D_data: axis {ax_key} has length {len(axis)}")

            rc = "column" if n == flip_array else "row"
            header_lines.append(
                f"{comment_char} first {rc} is {ax_key} in units {new_unit}"
            )

        LOG.debug(f"Data shape: {dataset._data.shape}")

        # Add corner nil
        xaxis = prepend(0.0, new_axes[axis_numbers[1]].flat)

        # Add axes to data
        data_lines = zip(new_axes[axis_numbers[0]].flat, dataset.data)

        # Put xaxis in
        temp = prepend(xaxis, data_lines)

        # Flatten each row
        temp = map(collapse, temp)

        if flip_array:
            return header_lines, transpose(temp)

        return header_lines, temp

    def process_ND_data(
        self,
        dataset: SingleDataset,
    ) -> tuple[list[str], Iterator[Iterator[float]]]:
        """Convert an N-dimensional array into text.

        Parameters
        ----------
        dataset : SingleDataset
            input dataset
        separator : str, optional
            character separating the number in the output, by default " "
        is_preview : bool, optional
            if True, limit the number of output rows and columns, by default False

        Returns
        -------
        list[str]
            Header lines.
        Iterator[Iterator[float]]
            Data table of x,y,z,... data

        """
        header_lines, comment_char = self.make_dataset_header(
            dataset, comment_character=self._comment
        )
        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}

        for n, ax_key in enumerate(dataset.available_x_axes()):
            axis_unit = dataset._axes_units[ax_key]
            new_unit = self._plotting_context.get_conversion_factor(axis_unit)
            conv_factor = measure(1.0, axis_unit, equivalent=True).toval(new_unit)

            axis = dataset._axes[ax_key]
            new_axes[ax_key] = conv_factor * axis
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key
            LOG.debug("process_ND_data: axis %s has length %d.", ax_key, len(axis))

        for ax_num, ax_key in enumerate(new_axes):
            header_lines.append(
                f"{comment_char} {ax_num} column is {ax_key} in units {new_axes_units[ax_key]}"
            )

        LOG.debug(f"Data shape: {dataset._data.shape}")

        ax_lengths = [len(new_axes[ax_num]) for ax_num in axis_numbers.values()]
        LOG.debug(f"Axis lengths: {ax_lengths}")
        LOG.debug(f"Axis sequence: {axis_numbers}")

        # Attach axis indices
        temp = zip(
            cart_prod(*(new_axes[ind] for ind in axis_numbers.values())),
            dataset.data.ravel(),
        )
        # Flatten each row
        temp = map(collapse, temp)

        return header_lines, temp


class Text(Plotter):
    """Special plotter producing text instead of plots.

    The Text plotter is technically not a plotter, since
    it outputs text. The main advantage of imitating a plotter
    is that Text can use the GUI settings of units.
    In the end, PlottingContext matches the dataset to
    the x (y and z, optionally) axes in the data file,
    and the plotting interface supplies the user selection
    of physical units.
    """

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._formatter = DatasetFormatter()
        self._curve_limit_per_dataset = 12
        self._pc_backup = None
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: QTextBrowser = None):
        """Clear the output text widget.

        Optionally sets the input to be the new
        text output widget, and then clears the
        currently stored text widget instance.

        Parameters
        ----------
        figure : QTextBrowser, optional
            optionally, new QTextBrowser to be used

        """
        LOG.debug("Text.clear stared")
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()
        LOG.debug("Text.clear finished")

    def adjust_formatter(
        self,
        preview=False,
        preview_lines=10,
        preview_columns=10,
        rounding=15,
        separator=" ",
        comment="#",
    ):
        """Pass the GUI settings to the text formatter."""
        if self._formatter is None or self._pc_backup is None or self._figure is None:
            return
        self._formatter._is_preview = preview
        self._formatter._preview_lines = preview_lines
        self._formatter._preview_columns = preview_columns
        self._formatter._rounding_prec = rounding
        self._formatter._separator = separator
        self._formatter._comment = comment
        self.plot(self._pc_backup, self._figure)

    def get_figure(self, figure: QTextBrowser = None):
        """Get the widget which will display the text.

        Used for both updating and getting the output widget
        which will be used for displaying the output text.

        Parameters
        ----------
        figure : QTextBrowser, optional
            New widget to be used for displaying text.
            If None, the currently stored widget will be used.

        Returns
        -------
        QTextBrowser or None
            If no widget reference can be used, returns None.
            Otherwise, returns a widget instance that should be used
            for displaying text.

        """
        LOG.debug("Text.get_figure stared")
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        LOG.debug("Text.get_figure finished")
        return target

    def apply_settings(self, plotting_context: PlottingContext, colours=None):
        """Do nothing.

        Not relevant to the Text plotter, added for compatibility

        Parameters
        ----------
        plotting_context : PlottingContext
            ignored
        colours : _type_, optional
            ignored

        """
        LOG.debug("Text.apply_settings called. Doing nothing")

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: QTextBrowser = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        """Show data as text.

        In the Text plotter, the plot method displays the data as text.
        Many arguments are included just for compatibility with the plotter.

        Parameters
        ----------
        plotting_context : PlottingContext
            Data model containing the data sets to be shown
        figure : QTextBrowser, optional
            Target widget, an instance of QTextBrowser
        colours : _type_, optional
            ignored here
        update_only : bool, optional
            ignored
        toolbar : _type_, optional
            ignored

        """
        LOG.debug("Text.plot stared")
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self._pc_backup = plotting_context
        self._figure = target
        _xaxis_unit = None
        self._active_curves = []
        self._backup_curves = []
        self.apply_settings(plotting_context, colours)
        self.height_max, self.length_max = 0.0, 0.0
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        if len(plotting_context.datasets()) == 0:
            target.clear()
            return
        self._formatter.take_new_input(plotting_context)
        target.setText("\n".join(self._formatter._new_text))
