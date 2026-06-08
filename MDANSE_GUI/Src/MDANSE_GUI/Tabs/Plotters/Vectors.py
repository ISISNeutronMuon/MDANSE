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
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from more_itertools import ilen

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlottingContext import PlotArgs
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure

    from MDANSE.util_types import FloatArray
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


def violin_plot_width(positions: FloatArray) -> float:
    """Return the width of the violin plot based on the spacing between points."""
    return np.mean(np.diff(positions)) if len(positions) > 1 else 0.5


@Plotter.register("Vectors")
class Vectors(Plotter):
    """Plots summarised Q-Vectors to one figure."""

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

    def slider_limits(self) -> list[tuple[float, float, float]]:
        """Return generic slider limit values."""
        return [(-1.0, 1.0, 0.01)] * self._number_of_sliders

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
            Parameters as in NORMALISATION_DEFAULTS.

        """
        super().change_normalisation(new_value)

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
        self._normalisation_errors = []
        self._axes = []
        self._active_curves = []
        self._backup_curves = []
        self.apply_settings(plotting_context)

        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        if not plotting_context.datasets():
            target.clear()
            self.plot_blank()
            return

        gs = self._figure.add_gridspec(2, 2)
        labels = iter(("Used", "Found"))

        for databundle in plotting_context.datasets().values():
            dataset = databundle.dataset

            plotlabel = databundle.legend_label
            x_axis_labels = [dataset.x_axis_label(databundle.main_axis)]

            match dataset._name:
                case "Available vectors":
                    axes = self._figure.add_subplot(gs[0, 0])

                    for _, curve in dataset.curves_vs_axis(databundle.main_axis):
                        lab = plotlabel if dataset._n_dim != 2 else next(labels)

                        axes.bar(
                            *curve,
                            label=lab,
                        )

                    axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                    axes.set_title(dataset._name)
                    self._axes.append(axes)

                case r"<|q|> - q$_{target}$":
                    axes = self._figure.add_subplot(gs[0, 1])
                    xvals = dataset.x_axis(databundle.main_axis)
                    axes.violinplot(
                        dataset.data,
                        positions=xvals,
                        widths=violin_plot_width(xvals),
                    )
                    self._axes.append(axes)
                    axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                    axes.set_title(dataset._name)

                case "Shell population":
                    axes = self._figure.add_subplot(gs[1, :])

                    n_curves = ilen(
                        dataset.curves_vs_axis(
                            databundle.main_axis,
                            max_limit=self._curve_limit_per_dataset,
                        )
                    )

                    x_axis = dataset.x_axis(databundle.main_axis)
                    bottom = np.zeros_like(x_axis)
                    width = 0.8 * abs(np.mean(np.diff(x_axis)))

                    self._axes.append(axes)

                    axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
                    for ind, (label, curve) in enumerate(
                        dataset.curves_vs_axis(
                            databundle.main_axis,
                            max_limit=self._curve_limit_per_dataset,
                        )
                    ):
                        try:
                            axes.bar(
                                *curve,
                                label=self.label(
                                    ind=ind,
                                    n_curves=n_curves,
                                    limit=self._legend_limit_for_histogram,
                                    label=f"{plotlabel}:{label}",
                                ),
                                bottom=bottom,
                                width=width,
                                edgecolor="black",
                            )
                            bottom += curve[1]

                        except ValueError:
                            x, y = curve
                            LOG.error(
                                f"Plotting failed for {plotlabel} using {databundle.main_axis}"
                            )
                            LOG.error(f"x_axis={x}")
                            LOG.error(f"values={y}")
                            raise

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
                        _, best_axis = dataset.longest_axis()
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
        self._figure.canvas.draw()
