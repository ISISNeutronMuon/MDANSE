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
import math
from itertools import islice
from typing import TYPE_CHECKING, Any

import numpy as np
from more_itertools import ilen

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    import numpy.typing as npt
    from matplotlib.axes import Axes
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlotArgs, PlottingContext


@Plotter.register("Grouped")
class Grouped(Plotter):
    """Plots each dataset in its own subplot."""

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._backup_limits: list[tuple[float, float, float, float]] = []
        self._active_curves: list[Line2D] = []
        self._backup_curves: list[
            tuple[npt.NDArray[np.floating], npt.NDArray[np.floating]]
        ] = []
        self._plot_limit = 9
        self.height_max, self.length_max = -np.inf, -np.inf

    def slider_labels(self) -> list[str]:
        """Return labels to show that sliders are not used."""
        return ["Y offset", "X offset"]

    def slider_limits(self) -> list[tuple[float, float, float]]:
        """Return generic slider limit values."""
        return [(-1.0, 1.0, 0.01)] * self._number_of_sliders

    def handle_slider(self, new_value: list[float]):
        """Save slider values and call offset_curves."""
        super().handle_slider(new_value)
        self.offset_curves()

    def offset_curves(self):
        """Offset curves against each other based on slider settings."""
        target = self._figure
        if target is None:
            return

        new_value = self._slider_values

        backup = iter(self._backup_curves)
        for ind, axes in enumerate(self._axes):
            saved_xmin, saved_xmax, saved_ymin, saved_ymax = self._backup_limits[ind]

            for num, curve in enumerate(axes.get_lines()):
                xdata, ydata = next(backup)
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

            axes.relim()
            axes.autoscale()

            self._backup_limits[ind] = (saved_xmin, saved_xmax, saved_ymin, saved_ymax)

            try:
                axes.set_xlim(saved_xmin, saved_xmax)
            except ValueError:
                LOG.error(
                    f"Matplotlib could not set x limits to {saved_xmin}, {saved_xmax}",
                )

            try:
                axes.set_ylim(saved_ymin, saved_ymax)
            except ValueError:
                LOG.error(
                    f"Matplotlib could not set y limits to {saved_ymin}, {saved_ymax}",
                )

        if self._toolbar is not None:
            self._toolbar.update()
            self._toolbar.push_current()

        target.canvas.draw()

    def check_curve_lengths(self):
        """Find the maximum number of elements in the x axes of the plot data."""
        self.curve_length_limit = 0
        for num, _ in enumerate(self._active_curves):
            xdata = self._backup_curves[num][0]
            self.curve_length_limit = max(self.curve_length_limit, len(xdata))

    def change_normalisation(self, new_value: dict[str, Any]):
        """Normalise the data based on the new parameters.

        Parameters
        ----------
        new_value : dict[str, Any]
            parameters as in NORMALISATION_DEFAULTS

        """
        super().change_normalisation(new_value)
        target = self._figure
        if target is None or not self._active_curves:
            return

        for curve_index, curve in enumerate(self._active_curves):
            xdata, ydata = self._backup_curves[curve_index]
            xdata, ydata = self.normalise_curve(xdata, ydata)
            curve.set_xdata(xdata)
            curve.set_ydata(ydata)

        target.canvas.draw()

        for axes in self._axes:
            axes.relim()
            axes.autoscale()

        if self._toolbar is not None:
            self._toolbar.update()
            self._toolbar.push_current()

    def toggle_legend(self, enabled: bool) -> None:
        if self._figure is None:
            return

        for axes, title in zip(self._axes, self._axes_titles, strict=True):
            axes.set_title(
                title if enabled else "",
                fontsize=self.title_fontsize(title),
            )
            axes.get_legend().set_visible(enabled)

        self._figure.canvas.draw()

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: Toolbar | None = None,
    ):
        """Plot datasets in separate subplots.

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

        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        self.height_max, self.length_max = 0.0, 0.0
        self._figure = target
        self._axes = []
        self._axes_titles = []
        self._backup_curves = []
        self._active_curves = []
        self._normalisation_errors = []
        self.apply_settings(plotting_context)

        nplots = min(ilen(plotting_context.curves()), self._plot_limit)
        grid_size = self.grid_size(nplots)
        gs = self._figure.add_gridspec(*grid_size)
        limits = [(0.0, 0.0, 0.0, 0.0) for _ in range(nplots)]

        for ind, (db, dataclump) in enumerate(
            islice(
                zip(
                    plotting_context.datasets().values(),
                    plotting_context.curves(),
                    strict=True,
                ),
                self._plot_limit,
            )
        ):
            ds = db.dataset
            axes = target.add_subplot(gs[ind])
            self._axes_titles.append(ds._name)

            colours = self.colours(db.colour, ds.n_curves)

            for (databundle, label, curve), colour in zip(
                dataclump, colours, strict=True
            ):
                self._plot_single(
                    axes,
                    curve,
                    databundle,
                    label=label,
                    colour=colour,
                )
            axes.legend()
            self._axes.append(axes)
            limits[ind] = (*axes.get_xlim(), *axes.get_ylim())

            if update_only:
                try:
                    axes.set_xlim(self._backup_limits[ind][:2])
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set x limits to {self._backup_limits[ind][:2]}"
                    )

                try:
                    axes.set_ylim(self._backup_limits[ind][2:])
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set y limits to {self._backup_limits[ind][2:]}"
                    )

        if not update_only:
            self._backup_limits = limits

        self.enable_slider(
            allow_slider=any(
                db.dataset.n_curves > 1 for db in plotting_context.datasets().values()
            )
        )
        self.toggle_legend(plotting_context.use_legend)
        self.toggle_grid(plotting_context.use_grid)

        self.apply_settings(plotting_context)
        self.check_curve_lengths()
        target.canvas.draw()

        if self._toolbar is not None:
            self._toolbar.update()
            self._toolbar.push_current()

    def _plot_single(
        self,
        axes: Axes,
        curve: tuple[np.ndarray, np.ndarray] | tuple[np.ndarray],
        databundle: PlotArgs,
        *,
        label: str,
        colour: tuple[float, float, float] | str,
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
        label : str
            Plot label.
        colour : tuple[float, float, float] | str
            Curve colour.
        """
        lines: list[Line2D] = axes.plot(
            *curve,
            linestyle=databundle.line_style,
            label=label,
            color=colour,
        )

        axes.set_xlabel(databundle.dataset.x_axis_label(databundle.main_axis))

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
