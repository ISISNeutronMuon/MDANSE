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

import contextlib
from collections.abc import Generator
from itertools import islice
from typing import TYPE_CHECKING, Any

import numpy as np
from more_itertools import flatten, ilen

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlotArgs, PlottingContext


@Plotter.register("Single")
class Single(Plotter):
    """Plots all the datasets in the same figure."""

    def __init__(self) -> None:
        """Initialise all ploting parameters to default values."""
        super().__init__()
        self._figure = None
        self._active_curves: list[Line2D] = []
        self._backup_curves: list[tuple[np.ndarray, np.ndarray]] = []
        self._backup_limits = []
        self._curve_limit_per_dataset = 12
        self._plot_limit = 60
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: Figure | None = None):
        """Clear the figure."""
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def get_figure(self, figure: Figure | None = None):
        """Return the figure instance used for plotting."""
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        return target

    def slider_labels(self) -> list[str]:
        """Return slider labels for single plot mode."""
        return ["Y offset", "X offset"]

    def slider_limits(self) -> list[tuple[float, float, float]]:
        """Return slider limits for single plot mode."""
        return [(-1.0, 1.0, 0.001)] * self._number_of_sliders

    def handle_slider(self, new_value: list[float]):
        """Save slider values and call offset_curves."""
        super().handle_slider(new_value)
        self.offset_curves()

    def change_normalisation(self, new_value: dict[str, Any]):
        """Normalise the data based on the new parameters.

        Parameters
        ----------
        new_value : dict[str, Any]
            Parameters as in NORMALISATION_DEFAULTS.
        """
        super().change_normalisation(new_value)
        self.offset_curves()

    def offset_curves(self):
        """Offset curves against each other based on slider settings."""
        target = self._figure
        if target is None or not self._active_curves:
            return

        new_value = self._slider_values
        saved_xmin, saved_xmax, saved_ymin, saved_ymax = self._backup_limits

        for num, curve in enumerate(self._active_curves):
            xdata, ydata = self._backup_curves[num]
            xdata, ydata = self.normalise_curve(xdata, ydata)
            new_xdata = xdata + num * self.length_max * new_value[1]
            new_ydata = ydata + num * self.height_max * new_value[0]
            curve.set_xdata(new_xdata)
            curve.set_ydata(new_ydata)
            xmin, xmax = np.nanmin(new_xdata), np.nanmax(new_xdata)
            ymin, ymax = np.nanmin(new_ydata), np.nanmax(new_ydata)
            saved_xmin = np.nanmin([xmin, saved_xmin])
            saved_xmax = np.nanmax([xmax, saved_xmax])
            saved_ymin = np.nanmin([ymin, saved_ymin])
            saved_ymax = np.nanmax([ymax, saved_ymax])
        self._backup_limits = [saved_xmin, saved_xmax, saved_ymin, saved_ymax]
        self._axes[0].relim()
        self._axes[0].autoscale()

        if self._toolbar is not None:
            self._toolbar.update()
            self._toolbar.push_current()

        try:
            self._axes[0].set_xlim(saved_xmin, saved_xmax)
        except ValueError:
            LOG.error(
                f"Matplotlib could not set x limits to {saved_xmin}, {saved_xmax}",
            )

        try:
            self._axes[0].set_ylim(saved_ymin, saved_ymax)
        except ValueError:
            LOG.error(
                f"Matplotlib could not set y limits to {saved_ymin}, {saved_ymax}",
            )
        target.canvas.draw()

    def check_curve_lengths(self):
        """Find the maximum number of elements in the x axes of the plot data."""
        self.curve_length_limit = 0
        for num, _ in enumerate(self._active_curves):
            xdata = self._backup_curves[num][0]
            self.curve_length_limit = max(self.curve_length_limit, len(xdata))

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: Toolbar | None = None,
    ):
        """Plot all datasets in the same figure.

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
        self.enable_slider(allow_slider=False)

        target = self.get_figure(figure)
        if target is None:
            return

        if toolbar is not None:
            self._toolbar = toolbar

        self._figure = target
        self._active_curves = []
        self._backup_curves = []
        self._normalisation_errors = []
        x_axis_labels = []

        self.apply_settings(plotting_context)

        self.height_max, self.length_max = 0.0, 0.0

        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        total_n_curves = sum(
            map(ilen, plotting_context.curves(self._curve_limit_per_dataset))
        )

        if not total_n_curves:
            self.plot_blank()
            return

        self.enable_slider(allow_slider=total_n_curves > 1)

        colours = {}
        for databundle in plotting_context.datasets().values():
            colours[databundle.row] = self.colours(
                databundle.colour, databundle.dataset.n_curves
            )
            x_axis_labels.append(databundle.dataset.x_axis_label(databundle.main_axis))

        axes = target.add_subplot(111)
        self._axes = [axes]

        for databundle, _, curve in islice(
            flatten(plotting_context.curves(self._curve_limit_per_dataset)),
            self._plot_limit,
        ):
            self._plot_single(
                axes,
                curve,
                databundle,
                colour=next(colours[databundle.row]),
            )

        if update_only:
            try:
                axes.set_xlim((self._backup_limits[0], self._backup_limits[1]))
            except ValueError:
                LOG.error(
                    f"Matplotlib could not set x limits to {self._backup_limits[0]}, {self._backup_limits[1]}"
                )

            try:
                axes.set_ylim((self._backup_limits[2], self._backup_limits[3]))
            except ValueError:
                LOG.error(
                    f"Matplotlib could not set y limits to {self._backup_limits[2]}, {self._backup_limits[3]}"
                )
        else:
            self._backup_limits = [*axes.get_xlim(), *axes.get_ylim()]

        axes.set_xlabel(", ".join(np.unique(x_axis_labels)))

        if plotting_context.use_legend:
            axes.legend()

        axes.grid(plotting_context.use_grid)
        self.check_curve_lengths()
        self.offset_curves()

    def _plot_single(
        self,
        axes: Axes,
        curve: tuple[np.ndarray, np.ndarray] | tuple[np.ndarray],
        databundle: PlotArgs,
        *,
        colour: tuple[float, float, float],
    ):
        """Plot a single curve to axes.

        Parameters
        ----------
        axes : Axes
            Axis to plot to.
        curve : tuple[np.ndarray, np.ndarray] | tuple[np.ndarray]
            Curve to plot.
        databundle : PlotArgs
            Data to plot.
        colour : tuple[float, float, float]
            Curve colour.
        """
        lines: list[Line2D] = axes.plot(
            *curve,
            linestyle=databundle.line_style,
            label=databundle.legend_label,
            color=colour,
        )

        for line in lines:
            try:
                line.set_marker(databundle.marker)
            except ValueError:
                with contextlib.suppress(Exception):
                    line.set_marker(int(databundle.marker))

            self.height_max = np.nanmax([self.height_max, np.nanmax(line.get_ydata())])
            self.length_max = np.nanmax([self.length_max, np.nanmax(line.get_xdata())])

        self._active_curves.extend(lines)
        self._backup_curves.extend(
            (line.get_xdata(), line.get_ydata()) for line in lines
        )
