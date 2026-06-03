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

from matplotlib import rcParams

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


@Plotter.register("Grid")
class Grid(Plotter):
    """Plots each curve in its own subplot."""

    slider_labels = "Inactive", "Inactive"

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._backup_limits = []
        self._active_curves = []
        self._backup_curves = []
        self._plot_limit = 8
        self._title_length_limit = 30

    def slider_limits(self) -> list[str]:
        """Return generic slider limit values."""
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

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
        if target is None:
            return
        if len(self._active_curves) == 0:
            return
        for curve_index, curve in enumerate(self._active_curves):
            xdata = self._backup_curves[curve_index][0]
            ydata = self._backup_curves[curve_index][1]
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

    def title_fontsize(self, title_text: str) -> int:
        normal_size = rcParams["font.size"]
        new_size = (
            normal_size
            if len(title_text) < self._title_length_limit
            else normal_size - round(len(title_text) / self._title_length_limit)
        )
        return new_size

    def toggle_legend(self, enabled: bool) -> None:
        if self._figure is None:
            return
        for plot_index, axes in enumerate(self._axes):
            axes.set_title(
                self._axes_titles[plot_index] if enabled else "",
                fontsize=self.title_fontsize(self._axes_titles[plot_index]),
            )
        self._figure.canvas.draw()

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure = None,
        update_only=False,
        toolbar=None,
    ):
        """Plot datasets in separate subplots.

        Parameters
        ----------
        plotting_context : PlottingContext
            Data model storing the data to be plotted
        figure : Figure, optional
            Matplotlib figure instance for plotting, by default None
        update_only : bool, optional
            If true, try to re-use zoom settings, by default False
        toolbar : _type_, optional
            GUI instance of the matplotlib toolbar, by default None

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
        self._figure = target
        self._axes = []
        self._axes_titles = []
        self._backup_curves = []
        self._active_curves = []
        self._normalisation_errors = []
        self.apply_settings(plotting_context)
        nplots = 0
        for databundle in plotting_context.datasets().values():
            ds = databundle.dataset
            try:
                axis_info = ds._axes_units[databundle.main_axis], databundle.main_axis
            except KeyError:
                axis_info = ds.longest_axis()
            curves = ds.curves_vs_axis(axis_info, max_limit=self._plot_limit)
            nplots += len(curves)
        nplots = min(nplots, self._plot_limit)
        gridsize = math.ceil(nplots**0.5)
        startnum = 1
        counter = 0
        for databundle in plotting_context.datasets().values():
            dataset = databundle.dataset
            try:
                _, best_axis = (
                    dataset._axes_units[databundle.main_axis],
                    databundle.main_axis,
                )
            except KeyError:
                _, best_axis = dataset.longest_axis()
            for key, curve in islice(dataset._curves.items(), self._plot_limit):
                counter += 1
                if counter > self._plot_limit:
                    LOG.warning(
                        "Curves above the current limit of %s will be ignored",
                        self._plot_limit,
                    )
                    break
                axes = target.add_subplot(gridsize, gridsize, startnum)
                self._axes.append(axes)
                plotlabel = databundle.legend_label
                if dataset._curve_labels[key]:
                    plotlabel += ":" + dataset._curve_labels[key]
                x_axis_label = dataset.x_axis_label(best_axis)
                [temp_curve] = axes.plot(
                    dataset.x_axis(best_axis),
                    curve,
                    linestyle=databundle.line_style,
                    color=databundle.colour,
                    label=plotlabel,
                )
                try:
                    temp_curve.set_marker(databundle.marker)
                except ValueError:
                    with contextlib.suppress(Exception):
                        temp_curve.set_marker(int(databundle.marker))
                axes.set_xlabel(x_axis_label)
                self._axes_titles.append(plotlabel)
                axes.set_title(
                    plotlabel if plotting_context.use_legend else "",
                    fontsize=self.title_fontsize(plotlabel),
                )
                legend = axes.legend()
                legend.set_visible(False)
                axes.grid(plotting_context.use_grid)
                startnum += 1
                self._active_curves.append(temp_curve)
                self._backup_curves.append(
                    [temp_curve.get_xdata(), temp_curve.get_ydata()],
                )
        if counter == 0:
            self.plot_blank()
            return
        self.apply_settings(plotting_context)
        self.check_curve_lengths()
        target.canvas.draw()
        if self._toolbar is not None:
            self._toolbar.update()
            self._toolbar.push_current()
