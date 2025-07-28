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
from typing import TYPE_CHECKING, Any

import numpy as np

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Single(Plotter):
    """Plots all the datasets in the same figure."""

    def __init__(self) -> None:
        """Initialise all ploting parameters to default values."""
        super().__init__()
        self._figure = None
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._curve_limit_per_dataset = 12
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: Figure = None):
        """Clear the figure."""
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def get_figure(self, figure: Figure = None):
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

    def slider_limits(self) -> list[str]:
        """Return slider limits for single plot mode."""
        return self._number_of_sliders * [[-1.0, 1.0, 0.001]]

    def handle_slider(self, new_value: list[float]):
        """Save slider values and call offset_curves."""
        super().handle_slider(new_value)
        self.offset_curves()

    def change_normalisation(self, new_value: dict[str, Any]):
        """Normalise the data based on the new parameters.

        Parameters
        ----------
        new_value : dict[str, Any]
            parameters as in NORMALISATION_DEFAULTS

        """
        super().change_normalisation(new_value)
        self.offset_curves()

    def offset_curves(self):
        """Offset curves against each other based on slider settings."""
        target = self._figure
        if target is None:
            return
        if len(self._active_curves) == 0:
            return
        new_value = self._slider_values
        saved_xmin, saved_xmax, saved_ymin, saved_ymax = self._backup_limits
        for num, curve in enumerate(self._active_curves):
            xdata = self._backup_curves[num][0]
            ydata = self._backup_curves[num][1]
            xdata, ydata = self.normalise_curve(xdata, ydata)
            new_xdata = xdata + num * self.length_max * new_value[1]
            new_ydata = ydata + num * self.height_max * new_value[0]
            curve.set_xdata(new_xdata)
            curve.set_ydata(new_ydata)
            xmin, xmax = new_xdata.min(), new_xdata.max()
            ymin, ymax = new_ydata.min(), new_ydata.max()
            saved_xmin = min(xmin, saved_xmin)
            saved_xmax = max(xmax, saved_xmax)
            saved_ymin = min(ymin, saved_ymin)
            saved_ymax = max(ymax, saved_ymax)
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
        figure: Figure = None,
        update_only=False,
        toolbar=None,
    ):
        """Plot all datasets in the same figure.

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
        self._figure = target
        self._active_curves = []
        self._backup_curves = []
        self._normalisation_errors = []
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context)
        x_axis_labels = []
        self.height_max, self.length_max = 0.0, 0.0
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        if len(plotting_context.datasets()) == 0:
            target.clear()
            target.canvas.draw()
        for databundle in plotting_context.datasets().values():
            dataset = databundle.dataset
            try:
                best_unit, best_axis = (
                    dataset._axes_units[databundle.main_axis],
                    databundle.main_axis,
                )
            except KeyError:
                best_unit, best_axis = dataset.longest_axis()
            plotlabel = databundle.legend_label
            x_axis_labels.append(dataset.x_axis_label(best_axis))
            if dataset._n_dim == 1:
                [temp] = axes.plot(
                    dataset.x_axis(best_axis),
                    dataset.data,
                    linestyle=databundle.line_style,
                    label=plotlabel,
                    color=databundle.colour,
                )
                try:
                    temp.set_marker(databundle.marker)
                except ValueError:
                    with contextlib.suppress(Exception):
                        temp.set_marker(int(databundle.marker))
                self._active_curves.append(temp)
                self._backup_curves.append([temp.get_xdata(), temp.get_ydata()])
                self.height_max = max(self.height_max, temp.get_ydata().max())
                self.length_max = max(self.length_max, temp.get_xdata().max())
            else:
                multi_curves = dataset.curves_vs_axis(
                    (best_unit, best_axis), max_limit=self._curve_limit_per_dataset
                )
                counter = 0
                for key, value in multi_curves.items():
                    counter += 1
                    if counter >= self._curve_limit_per_dataset:
                        break
                    try:
                        [temp] = axes.plot(
                            dataset.x_axis(best_axis),
                            value,
                            label=plotlabel + ":" + dataset._curve_labels[key],
                        )
                        self._active_curves.append(temp)
                        self._backup_curves.append([temp.get_xdata(), temp.get_ydata()])
                        self.height_max = max(self.height_max, temp.get_ydata().max())
                        self.length_max = max(self.length_max, temp.get_xdata().max())
                    except ValueError:
                        LOG.error(f"Plotting failed for {plotlabel} using {best_axis}")
                        LOG.error(f"x_axis={dataset._axes[best_axis]}")
                        LOG.error(f"values={value}")
                        return
        if len(self._backup_curves) > 1:
            self.enable_slider(allow_slider=True)
        elif not self._backup_curves:
            self.plot_blank()
            return
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
            xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
            self._backup_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
        if plotting_context.use_legend:
            axes.legend()
        axes.grid(plotting_context.use_grid)
        self.check_curve_lengths()
        self.offset_curves()
