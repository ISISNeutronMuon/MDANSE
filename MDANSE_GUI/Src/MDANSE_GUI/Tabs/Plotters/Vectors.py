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
import numpy.typing as npt

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


def violin_plot_width(positions: npt.NDArray[float]) -> float:
    """Return the width of the violin plot based on the spacing between points."""
    return np.mean(np.diff(positions)) if len(positions) > 1 else 0.5


class Vectors(Plotter):
    """Plots all the datasets in the same figure."""

    def __init__(self) -> None:
        """Initialise all ploting parameters to default values."""
        super().__init__()
        self._figure = None
        self._backup_limits = {}
        self._curve_limit_per_dataset = 128
        self._legend_limit_for_histogram = 6

    def slider_labels(self) -> list[str]:
        """Return labels to show that sliders are not used."""
        return ["Inactive", "Inactive"]

    def slider_limits(self) -> list[str]:
        """Return generic slider limit values."""
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

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

    def change_normalisation(self, new_value: dict[str, Any]):
        """Normalise the data based on the new parameters.

        Parameters
        ----------
        new_value : dict[str, Any]
            parameters as in NORMALISATION_DEFAULTS

        """
        super().change_normalisation(new_value)

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: type | None = None,
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
        self._normalisation_errors = []
        self._axes = []
        self.apply_settings(plotting_context)
        x_axis_labels = []
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        if not plotting_context.datasets():
            target.clear()
            target.canvas.draw()
        single_plot_stack = [222, 221]
        label_stack = [
            "Used",
            "Found",
        ]
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
            if dataset._name == "Available vectors":
                axes = target.add_subplot(single_plot_stack.pop())
                if dataset._n_dim == 2:
                    temp_curves = []
                    for value in dataset.data.T:
                        [temp] = axes.plot(
                            dataset.x_axis(best_axis),
                            value,
                            label=label_stack.pop(),
                        )
                        temp_curves.append(temp)
                        if not label_stack:
                            break
                else:
                    temp_curves = axes.plot(
                        dataset.x_axis(best_axis),
                        dataset.data,
                        linestyle=databundle.line_style,
                        label=plotlabel,
                        color=databundle.colour,
                    )
                for temp in temp_curves:
                    try:
                        temp.set_marker(databundle.marker)
                    except ValueError:
                        with contextlib.suppress(Exception):
                            temp.set_marker(int(databundle.marker))
                self._axes.append(axes)
                axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                axes.set_title(dataset._name)
            elif dataset._name == r"<|q|> - q$_{target}$":
                axes = target.add_subplot(single_plot_stack.pop())
                xvals = dataset.x_axis(best_axis)
                axes.violinplot(
                    dataset.data,
                    positions=xvals,
                    widths=violin_plot_width(xvals),
                )
                self._axes.append(axes)
                axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                axes.set_title(dataset._name)
            elif dataset._name == "Shell population":
                axes = target.add_subplot(212)
                multi_curves = dataset.curves_vs_axis(
                    (best_unit, best_axis),
                    max_limit=self._curve_limit_per_dataset,
                )
                x_axis = dataset.x_axis(best_axis)
                bottom = np.zeros(len(x_axis))
                width = 0.8 * abs(np.mean(x_axis[1:] - x_axis[:-1]))
                self._axes.append(axes)
                add_legend_placeholder = (
                    len(multi_curves) > self._legend_limit_for_histogram
                )
                add_last_entry = False
                axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                for bar_index, (key, value) in enumerate(multi_curves.items()):
                    legend_label = plotlabel + ":" + dataset._curve_labels[key]
                    try:
                        axes.bar(
                            x_axis,
                            value,
                            label=legend_label
                            if bar_index < self._legend_limit_for_histogram
                            or add_last_entry
                            else None,
                            bottom=bottom,
                            width=width,
                            edgecolor="black",
                        )
                        bottom += value
                    except ValueError:
                        LOG.error(f"Plotting failed for {plotlabel} using {best_axis}")
                        LOG.error(f"x_axis={dataset._axes[best_axis]}")
                        LOG.error(f"values={value}")
                        return
                    else:
                        if (
                            add_legend_placeholder
                            and bar_index == len(multi_curves) - 2
                        ):
                            add_legend_placeholder = False
                            add_last_entry = True
                            axes.bar(
                                x_axis,
                                0,
                                label="...",
                                color=target.get_facecolor(),
                            )
        for axindex, axes in enumerate(self._axes):
            if update_only:
                plot_limits = self._backup_limits[axindex]
                if axindex != 1:  # axindex 1 is a special dataset for the violin plot.
                    try:
                        axes.set_xlim((plot_limits[0], plot_limits[1]))
                    except ValueError:
                        LOG.error(
                            f"Matplotlib could not set x limits to {plot_limits[0]}, {plot_limits[1]}",
                        )
                else:
                    for databundle in plotting_context.datasets().values():
                        dataset = databundle.dataset
                        best_unit, best_axis = dataset.longest_axis()
                        if dataset._name == r"<|q|> - q$_{target}$":
                            axes.clear()
                            xvals = dataset.x_axis(best_axis)
                            axes.violinplot(
                                dataset.data,
                                positions=xvals,
                                widths=violin_plot_width(xvals),
                            )
                            axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                            axes.set_title(dataset._name)
                try:
                    axes.set_ylim((plot_limits[2], plot_limits[3]))
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set y limits to {self._backup_limits[2]}, {self._backup_limits[3]}",
                    )
            else:
                xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
                self._backup_limits[axindex] = [
                    xlimits[0],
                    xlimits[1],
                    ylimits[0],
                    ylimits[1],
                ]
        for axes in self._axes:
            legend = axes.legend()
            legend.set_visible(plotting_context.use_legend)
            axes.grid(plotting_context.use_grid)
            axes.relim()
            axes.autoscale()
        if self._toolbar is not None:
            self._toolbar.update()
        target.canvas.draw()
