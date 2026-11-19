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
from typing import TYPE_CHECKING, ClassVar

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from qtpy.QtWidgets import QTextBrowser

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlotArgs, PlottingContext

FIXED_UNITS = {"rlu"}


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
        self._separator = ","

    def take_new_input(self, pc: PlottingContext | None):
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
                databundle,
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
            yield self.process_data(databundle, main_axis=databundle.main_axis)

    def join_for_gui(
        self,
        header_lines: list[str],
        data_array: Iterator[Iterator[float]],
        separator: str = ",",
    ):
        """Combine the header text with the data array into a string."""
        if self._is_preview:
            data = islice(data_array, self._preview_lines)
            data = (islice(x, self._preview_columns) for x in data)
        else:
            data = data_array

        text_data = "\n".join(
            separator.join(
                str(round(x, self._rounding_prec))
                if hasattr(x, "__round__")
                else str(x)
                for x in line
            )
            for line in data
        )

        # If not empty
        if self._is_preview and next(data_array, None) is not None:
            text_data += "\n..."

        new_header = "\n".join(header_lines)
        return new_header + "\n" + text_data

    def process_data(
        self,
        databundle: PlotArgs,
        main_axis: str | None = None,
    ):
        """Wrapper for appropriately handling ND data."""
        assert self._plotting_context

        return databundle.dataset.process_data(
            comment_character=self._comment,
            main_axis=main_axis,
            units=self._plotting_context._unit_preference,
        )


@Plotter.register("Text")
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

    _curve_limit_per_dataset: ClassVar[int] = 12

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._formatter = DatasetFormatter()
        self._pc_backup = None
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: QTextBrowser | None = None):
        """Clear the output text widget.

        Optionally sets the input to be the new
        text output widget, and then clears the
        currently stored text widget instance.

        Parameters
        ----------
        figure : QTextBrowser, optional
            optionally, new QTextBrowser to be used

        """
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def adjust_formatter(
        self,
        preview=False,
        preview_lines=10,
        preview_columns=10,
        rounding=15,
        separator=",",
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

    def get_figure(self, figure: QTextBrowser | None = None):
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
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        return target

    def apply_settings(self, plotting_context: PlottingContext):
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
        figure: QTextBrowser | None = None,
        *,
        update_only: bool = False,
        toolbar: Toolbar | None = None,
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
        colours : None, optional
            Ignored here
        update_only : bool, optional
            Ignored
        toolbar : Toolbar, optional
            Ignored.

        """
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
        self.apply_settings(plotting_context)
        self.height_max, self.length_max = 0.0, 0.0

        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        if len(plotting_context.datasets()) == 0:
            target.clear()
            return

        self._formatter.take_new_input(plotting_context)
        target.setText("\n".join(self._formatter._new_text))
