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
import csv
import enum
import math
from itertools import count
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TextIO

import numpy as np
from matplotlib import rcParams
from matplotlib.colors import to_rgb
from more_itertools import consumer

from MDANSE.Core.RegisterFactory import RegisterFactory
from MDANSE.IO.IOUtils import UCDict, UCEnum
from MDANSE.MLogging import LOG
from MDANSE.util_types import FloatArray

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator

    from matplotlib.axes import Axes
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class NormOperations(UCEnum):
    """Enum for selecting mathematical operations when calculating norms."""

    AVERAGE = enum.auto()
    SUM = enum.auto()
    NOT_IMPLEMENTED = enum.auto()

    @classmethod
    def _missing_(cls, value: str) -> NormOperations:
        if res := super()._missing_(value):
            return res
        return cls.NOT_IMPLEMENTED


def str_to_enum(operation: str) -> NormOperations:
    """Get the right enum from the input text string.

    Parameters
    ----------
    operation : str
        Name of the mathematical operation as string.

    Returns
    -------
    NormOperations
        Enum value of the operation.

    """
    return NormOperations(operation)


def enum_to_str(operation: NormOperations) -> str:
    """Convert the enum to a text string for the GUI.

    Parameters
    ----------
    operation : NormOperations
        Enum of the mathematical operation.

    Returns
    -------
    str
        Name of the operation as string.

    """
    return operation.name.lower()


NORMALISATION_DEFAULTS = {
    "apply": False,
    "min_index": 0,
    "max_index": 1,
    "operation": NormOperations.AVERAGE,
}

ValidPlotters = Literal["Single", "Vectors", "Text", "Heatmap", "Grid"]


class Plotter(RegisterFactory):
    """Parent class to all classes used for displaying data."""

    registry: ClassVar[UCDict[str, type[Plotter]]] = UCDict()

    GRID_SIZES = {
        2: (2, 1),
        5: (2, 3),
        6: (2, 3),
    }
    _title_length_limit: ClassVar[int] = 30
    _max_labels = 5

    def __init__(self) -> None:
        """Create defaults common to all plotters."""
        self._figure = None
        self._axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None
        self._slider_reference = None
        self.curve_length_limit = 10
        self._normalisation_values = copy.copy(NORMALISATION_DEFAULTS)
        self._normalisation_errors = []
        self._n_curves = 0

    def request_slider_values(self):
        """Manually read values from sliders, if they are present."""
        if self._slider_reference is None:
            return
        self._slider_reference.collect_values()

    def clear(self, figure: Figure | None = None):
        """Clear the figure, usually before plotting again.

        Parameters
        ----------
        figure : Figure, optional
            Figure to be cleared. If None, clear the internally stored figure.
            By default None

        """
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> list[str]:
        """Get text to be shown next to sliders."""
        return ["Slider 1", "Slider 2"]

    def slider_limits(self) -> list[tuple[float, float, float]]:
        """Get default limit values for sliders."""
        return [(-1.0, 1.0, 0.01)] * self._number_of_sliders

    def sliders_coupled(self) -> bool:
        """Check if the slider values depend on each other."""
        return False

    def get_figure(self, figure: Figure | None = None):
        """Get the reference to the current figure, if present."""
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        return target

    def apply_settings(self, plotting_context: PlottingContext):
        """Check that the plotting context can be used."""
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

    def toggle_grid(self, enabled: bool) -> None:
        if self._figure is None:
            return
        for axes in self._axes:
            axes.grid(enabled)
        self._figure.canvas.draw()

    def toggle_legend(self, enabled: bool) -> None:
        if self._figure is None:
            return
        for axes in self._axes:
            axes.get_legend().set_visible(enabled)
        self._figure.canvas.draw()

    def enable_slider(self, *, allow_slider: bool = True):
        """Enable or disable sliders.

        Parameters
        ----------
        allow_slider : bool, optional
            It True, sliders will become active, by default True

        """
        self._slider_reference.setEnabled(allow_slider)
        self._slider_reference.blockSignals(not allow_slider)

    def handle_slider(self, new_value: list[float]):
        """Respond to new slider values."""
        self._slider_values = new_value

    def normalise_curve(
        self, xdata: FloatArray, ydata: FloatArray
    ) -> tuple[FloatArray, FloatArray]:
        """Scale a 1D curve according to the current normalisation parameters.

        Parameters
        ----------
        xdata : FloatArray
            1D array of x values of the curve
        ydata : FloatArray
            1D array of y values of the curve

        Returns
        -------
        tuple[FloatArray]
            xdata and ydata with scaling applied

        """
        apply = self._normalisation_values["apply"]
        operation = self._normalisation_values["operation"]
        if not apply or operation is NormOperations.NOT_IMPLEMENTED:
            return xdata, ydata

        min_index = self._normalisation_values["min_index"]
        max_index = self._normalisation_values["max_index"]
        ref_values = ydata[min_index:max_index]

        if len(ref_values) < 1:
            self._normalisation_errors.append(
                "No points within the specified index range"
            )
            return xdata, ydata

        if operation is NormOperations.AVERAGE:
            scale_factor = np.nanmean(ref_values)
        elif operation is NormOperations.SUM:
            scale_factor = np.sum(np.nan_to_num(ref_values))

        if np.isclose(scale_factor, 0.0):
            self._normalisation_errors.append(
                "Normalisation factor is 0 and will not be applied."
            )
            return xdata, ydata

        return xdata, ydata / scale_factor

    def normalise_array(self, data_array: FloatArray) -> FloatArray:
        """Normalise a 2D array according to the current normalisation parameters.

        Parameters
        ----------
        data_array : FloatArray
            2D array of data for plotting

        Returns
        -------
        FloatArray
            the data_array with new relative intensities between rows

        """
        apply = self._normalisation_values["apply"]
        operation = self._normalisation_values["operation"]
        if not apply or operation == NormOperations.NOT_IMPLEMENTED:
            return data_array
        min_index = self._normalisation_values["min_index"]
        max_index = self._normalisation_values["max_index"]
        ref_column = data_array[:, min_index:max_index]
        if ref_column.shape[1] < 1:
            return data_array

        if operation is NormOperations.AVERAGE:
            scale_column = np.nanmean(ref_column, axis=1)
        elif operation is NormOperations.SUM:
            scale_column = np.sum(np.nan_to_num(ref_column), axis=1)

        if np.any(np.isclose(scale_column, 0.0)):
            self._normalisation_errors.append(
                "Normalisation factor is 0 for some rows of the 2D array."
            )
            return data_array

        return data_array / scale_column.reshape((len(scale_column), 1))

    def change_normalisation(self, new_value: dict[str, Any]):
        """Respond to new normalisation values."""
        self._normalisation_errors = []
        self._normalisation_values = new_value

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: Toolbar | None = None,
    ):
        """Plot the selected data in the figure.

        Parameters
        ----------
        plotting_context : PlottingContext
            Data model storing the data to be plotted.
        figure : Figure, optional
            Matplotlib figure instance for plotting, by default None.
        update_only : bool, optional
            If true, try to re-use zoom settings, by default False.
        toolbar : Toolbar, optional
            GUI instance of the matplotlib toolbar, by default None.

        """
        LOG.info(f"normalisation errors {self._normalisation_errors}, setting to []")
        self._normalisation_errors = []
        if (target := self.get_figure(figure)) is None:
            return

        if toolbar is not None:
            self._toolbar = toolbar

        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context)

    def plot_blank(
        self,
        *,
        draw_cross: bool = True,
        override_title: str | None = None,
        override_label: str | None = None,
    ):
        """Inform the user that no data could be plotted.

        Parameters
        ----------
        draw_cross : bool, optional
            If True, plot two intersecting lines to indicate visually that plotting was not possible, by default True
        """
        figure = self.get_figure()
        axes = figure.add_subplot(111)
        if draw_cross:
            axes.axline([0, 0], [1, 1], color="k", linestyle="-")
            axes.axline([0, 1], [1, 0], color="k", linestyle="-")
        label_text = (
            override_label
            or "If you expected a plot, please check the settings you changed last."
        )
        title_text = (
            override_title or "The data sets you selected could not be plotted."
        )
        axes.set_title(title_text)
        axes.set_xlabel(label_text)
        figure.canvas.draw()

    @staticmethod
    def save_name(
        out_file: str, axis: str | int = "N/A", line: str | int = "N/A"
    ) -> str:
        """Get standardised output filename.

        Parameters
        ----------
        out_file : str
            Filename template to use.
        axis : str | int
            Axis name.
        line : str | int
            Line name.
        """
        return out_file.replace("%axis%", str(axis)).replace("%line%", str(line))

    @consumer
    def _save_files(self, out_file: str):
        """Get next instance of file to write.

        If axes or line are to be updated will
        open new files when necessary, returning
        previous when unnecessary.

        Parameters
        ----------
        out_file : str
            Filename template to use.
        """
        line = "%line%" in out_file
        axis = "%axis%" in out_file

        new_axis, new_line = int(axis), int(line)

        while True:
            new_file = self.save_name(out_file, new_axis, new_line)
            LOG.info("Saving plot data to %s.", new_file)
            with open(new_file, "w", encoding="utf-8") as file:
                old_axis, old_line = new_axis, new_line
                while (new_axis, new_line) == (old_axis, old_line):
                    new_axis, new_line = yield file
                    new_axis, new_line = new_axis * axis, new_line * line

    @staticmethod
    def _write_save_data(
        file: TextIO,
        axis: Axes,
        line: Line2D,
        ax_ind: int,
        line_ind: int,
    ) -> None:
        """Write structured save data to csv file.

        Parameters
        ----------
        file : TextIO
            File to write to.
        axis : Axes
            Axis to write.
        line : Line2D
            Line to write.
        ax_ind : int
            Index of axis.
        line_ind : int
            Index of line.
        """
        title = axis.get_title() or ax_ind
        xlabel = axis.get_xlabel()
        ylabel = axis.get_ylabel()

        writer = csv.writer(file)
        eol = writer.dialect.lineterminator

        file.write(f"# Axis: {title}; Line: {line._label or line_ind}{eol}")

        writer.writerow((xlabel or "index", ylabel or "value"))
        writer.writerows(line.get_xydata())

        file.write(eol)

    def save_data(self, out_file: str) -> None:
        """Save lines to file.

        Parameters
        ----------
        out_file : str
            File to write data to.
        """
        file_gen = self._save_files(out_file)

        for ax_ind, axis in enumerate(self._figure.axes, 1):
            for li_ind, line in enumerate(self._get_datasets(axis), 1):
                file = file_gen.send((ax_ind, li_ind))
                self._write_save_data(file, axis, line, ax_ind, li_ind)

    @staticmethod
    def _get_datasets(axis: Axes) -> Iterator[Line2D]:
        """Yield datasets from axis.

        Parameters
        ----------
        axis : Axes
            Axis to use.

        Yields
        ------
        Line2D
            Each line in dataset.
        """
        yield from axis.get_lines()

    @classmethod
    def grid_size(cls, n_plots: int) -> tuple[int, int]:
        """Get a good grid layout for plotting.

        Parameters
        ----------
        n_plots : int
            Number of expected plots.

        Returns
        -------
        tuple[int, int]
            Grid size.
        """
        return cls.GRID_SIZES.get(n_plots, (math.ceil(n_plots**0.5),) * 2)

    def label(
        self,
        label: str,
        ind: int,
        *,
        n_curves: int | None = None,
        limit: int | None = None,
    ) -> str | None:
        """Get label for legend.

        For the abbreviated legend return None for those which are
        between ``limit`` and ``n_curves`` (skipping them), and "..."
        when it's at the limit.

        Parameters
        ----------
        ind : int
            Current index.
        n_curves : int
            Total number of "curves" to plot.
        limit : int
            Max number of entries in legend.
        label : str
            Current label.
        """
        if n_curves is None:
            n_curves = self.n_curves
        if limit is None:
            limit = self._max_labels

        if ind == limit:
            return "..."
        if limit < ind < n_curves - 1:
            return None
        return label

    @property
    def n_curves(self) -> int:
        """Number of expected/total curves."""
        return self._n_curves

    @staticmethod
    def colours(colour: str, n_curves: int) -> Generator[tuple[float, float, float]]:
        """Generate colours from root colour.

        Parameters
        ----------
        colour : str
            Root colour.

        Returns
        -------
        Generator[tuple[float, float, float]]
            Next colour in sequence.
        """
        main_colour = np.array(to_rgb(colour))
        colour_increment = (0.5 - main_colour) / n_curves
        for _ in range(n_curves):
            yield tuple(main_colour)
            main_colour += colour_increment

    def title_fontsize(self, title_text: str) -> int:
        normal_size = rcParams["font.size"]
        new_size = (
            normal_size
            if len(title_text) < self._title_length_limit
            else normal_size - round(len(title_text) / self._title_length_limit)
        )
        return new_size
