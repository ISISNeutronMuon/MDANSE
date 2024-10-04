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
from typing import TYPE_CHECKING, List
from functools import reduce
from itertools import product

import numpy as np

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QTextBrowser
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset


class DatasetFormatter:
    """Independent of the GUI component, DatasetFormatter
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

    def take_new_input(self, pc: "PlottingContext"):
        """The plotting context is passed from the GUI and
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
        List[str]
            A list of (multi-line) text strings, one per dataset
        """
        self._plotting_context = pc
        self._new_text = []
        if self._plotting_context is None:
            return ["No data selected"]
        for name, databundle in self._plotting_context.datasets().items():
            dataset, _, _, _, _ = databundle
            if dataset._n_dim == 1:
                header, data = self.process_1D_data(
                    dataset, separator=self._separator, is_preview=self._is_preview
                )
                self._new_text.append(
                    self.join_for_gui(header, data, separator=self._separator)
                )
            elif dataset._n_dim == 2:
                header, data = self.process_2D_data(
                    dataset,
                    name,
                    separator=self._separator,
                    is_preview=self._is_preview,
                )
                self._new_text.append(
                    self.join_for_gui(header, data, separator=self._separator)
                )
            else:
                header, data = self.process_ND_data(
                    dataset,
                    name,
                    separator=self._separator,
                    is_preview=self._is_preview,
                )
                self._new_text.append(
                    self.join_for_gui(header, data, separator=self._separator)
                )
        return self._new_text

    def datasets_for_csv(self):
        if self._plotting_context is None:
            return ["No data selected"]
        for name, databundle in self._plotting_context.datasets().items():
            dataset, _, _, _, _ = databundle
            if dataset._n_dim == 1:
                header, data = self.process_1D_data(dataset, separator=self._separator)
            elif dataset._n_dim == 2:
                header, data = self.process_2D_data(
                    dataset, name, separator=self._separator
                )
            else:
                header, data = self.process_ND_data(
                    dataset, name, separator=self._separator
                )
            yield header, data

    def make_dataset_header(self, dataset: "SingleDataset", comment_character="#"):
        """Extracts information related to the input dataset, and converts them
        into text. Returns a list of strings.

        Parameters
        ----------
        dataset : SingleDataset
            A dataset from MDANSE analysis results.
        comment_character : str, optional
            character used as prefix of the text header, by default '#'

        Returns
        -------
        List[str]
            list of header lines
        """
        lines = []
        lines.append(f"{comment_character} Dataset name: {dataset._name}")
        lines.append(f"{comment_character} from file {dataset._filename}")
        lines.append(
            f"{comment_character} Contains axes: "
            + ", ".join([str(axis) for axis in dataset.available_x_axes()])
        )
        lines.append(f"{comment_character} data unit is {dataset._data_unit}")
        return lines, comment_character

    def join_for_gui(
        self, header_lines: List[str], data_array: np.ndarray, separator=" "
    ):
        text_data = "\n".join(
            [
                separator.join([str(round(x, self._rounding_prec)) for x in line])
                for line in data_array
            ]
        )
        if self._is_preview:
            text_data += "\n..."
        new_header = "\n".join(header_lines)
        return new_header + "\n" + text_data

    def process_1D_data(
        self, dataset: "SingleDataset", separator=" ", is_preview=False
    ):
        """Formats a 1D array as a 2-column table with a commented header.
        The first column is determined using the information stored
        in the PlottingContext.

        Parameters
        ----------
        dataset : SingleDataset
            A SingleDataset read from an .MDA file (HDF5)
        separator : str, optional
            character(s) separating numbers in the output table, by default " "

        Returns
        -------
        str
            a data table with 2 columns in text format
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
        except:
            return f"Could not convert {best_unit} to {xaxis_unit}."
        else:
            header_lines.append(f"{self._comment} units of x axis here: {xaxis_unit}")
            header_lines.append(
                f"{self._comment} col1:{best_axis}:{xaxis_unit} col2:data:{dataset._data_unit}"
            )
            if is_preview:
                temp = np.vstack(
                    [
                        dataset._axes[best_axis][: self._preview_lines]
                        * conversion_factor,
                        dataset._data[: self._preview_lines],
                    ]
                ).T
            else:
                temp = np.vstack(
                    [dataset._axes[best_axis] * conversion_factor, dataset._data]
                ).T
            return header_lines, temp

    def process_2D_data(
        self, dataset: "SingleDataset", name: str, separator=" ", is_preview=False
    ):
        header_lines, comment_char = self.make_dataset_header(
            dataset, comment_character=self._comment
        )
        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}
        for n, ax_key in enumerate(dataset.available_x_axes()):
            axis = dataset._axes[ax_key]
            axis_unit = dataset._axes_units[ax_key]
            new_unit = self._plotting_context.get_conversion_factor(axis_unit)
            conv_factor = measure(1.0, axis_unit, equivalent=True).toval(new_unit)
            new_axes[ax_key] = conv_factor * axis
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key
            LOG.debug(f"process_2D_data: axis {ax_key} has length {len(axis)}")
            if n == 0:
                header_lines.append(
                    f"{comment_char} first column is {ax_key} in units {new_unit}"
                )
            else:
                header_lines.append(
                    f"{comment_char} first row is {ax_key} in units {new_unit}"
                )
        LOG.debug(f"Data shape: {dataset._data.shape}")
        if is_preview:
            nlines = self._preview_lines
            ncols = self._preview_columns
            nlines = min(nlines, len(new_axes[axis_numbers[0]]))
            ncols = min(ncols, len(new_axes[axis_numbers[1]]))
            temp = np.hstack(
                [
                    new_axes[axis_numbers[0]][:nlines].reshape((nlines, 1)),
                    dataset._data[:nlines, :ncols],
                ]
            )
            temp = np.vstack(
                [
                    np.concatenate([[0], new_axes[axis_numbers[1]][:ncols]]).reshape(
                        (1, ncols + 1)
                    ),
                    temp,
                ]
            )
        else:
            temp = np.hstack(
                [
                    new_axes[axis_numbers[0]].reshape((dataset._data.shape[0], 1)),
                    dataset._data,
                ]
            )
            temp = np.vstack(
                [
                    np.concatenate([[0], new_axes[axis_numbers[1]]]).reshape(
                        (1, dataset._data.shape[1] + 1)
                    ),
                    temp,
                ]
            )
        return header_lines, temp

    def process_ND_data(
        self, dataset: "SingleDataset", name: str, separator=" ", is_preview=False
    ):
        header_lines, comment_char = self.make_dataset_header(
            dataset, comment_character=self._comment
        )
        new_axes = {}
        new_axes_units = {}
        axis_numbers = {}
        for n, ax_key in enumerate(dataset.available_x_axes()):
            axis = dataset._axes[ax_key]
            axis_unit = dataset._axes_units[ax_key]
            new_unit = self._plotting_context.get_conversion_factor(axis_unit)
            conv_factor = measure(1.0, axis_unit, equivalent=True).toval(new_unit)
            new_axes[ax_key] = conv_factor * axis
            new_axes_units[ax_key] = new_unit
            axis_numbers[n] = ax_key
            LOG.debug(f"process_ND_data: axis {ax_key} has length {len(axis)}")
        for ax_num, ax_key in enumerate(new_axes.keys()):
            header_lines.append(
                f"{comment_char} {ax_num} column is {ax_key} in units {new_axes_units[ax_key]}"
            )
        LOG.debug(f"Data shape: {dataset._data.shape}")
        temp = []
        ncols = len(new_axes) + 1
        ax_lengths = [len(new_axes[ax_num]) for ax_num in axis_numbers.values()]
        total_lines = reduce(lambda x, y: x * y, ax_lengths)
        if is_preview:
            counter = 0
            nlines = self._preview_lines
        else:
            counter = 0
            nlines = total_lines
        all_indices = product(*[range(ax_lengths[n]) for n in axis_numbers.keys()])
        while counter < nlines:
            array_index = all_indices.__next__()
            xvals = [
                new_axes[axis_numbers[axis_number]][index]
                for axis_number, index in enumerate(array_index)
            ]
            yval = dataset._data[array_index]
            temp.append(xvals + [yval])
            counter += 1
        return header_lines, np.vstack(temp)


class Text(Plotter):
    """The Text plotter is technically not a plotter, since
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

    def clear(self, figure: "QTextBrowser" = None):
        """Optionally sets the input to be the new
        text output widget, and then clears the
        currently stored text widget instance.

        Parameters
        ----------
        figure : QTextBrowser, optional
            optionally, new QTextBrowser to be used
        """
        LOG.debug("Text.clear stared")
        if figure is None:
            target = self._figure
        else:
            target = figure
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
        if self._formatter is None or self._pc_backup is None or self._figure is None:
            return
        self._formatter._is_preview = preview
        self._formatter._preview_lines = preview_lines
        self._formatter._preview_columns = preview_columns
        self._formatter._rounding_prec = rounding
        self._formatter._separator = separator
        self._formatter._comment = comment
        self.plot(self._pc_backup, self._figure)

    def get_figure(self, figure: "QTextBrowser" = None):
        """Used for both updating and getting the output widget
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
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        LOG.debug("Text.get_figure finished")
        return target

    def apply_settings(self, plotting_context: "PlottingContext", colours=None):
        """Not relevant to the Text plotter, added for compatibility

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
        plotting_context: "PlottingContext",
        figure: "QTextBrowser" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        """In the Text plotter, the plot method displays the data as text.
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
        xaxis_unit = None
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
