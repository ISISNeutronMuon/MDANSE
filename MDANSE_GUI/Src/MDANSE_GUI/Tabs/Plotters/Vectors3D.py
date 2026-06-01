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
    from matplotlib.backends.backend_qt import NavigationToolbar2QT
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


@Plotter.register("Vectors3D")
class Vectors3D(Plotter):
    """Plots all the datasets in the same figure."""

    def __init__(self) -> None:
        """Initialise all ploting parameters to default values."""
        super().__init__()
        self._figure = None
        self._backup_limits = []
        self._curve_limit_per_dataset = 36
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
            parameters as in NORMALISATION_DEFAULTS

        """
        super().change_normalisation(new_value)

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: NavigationToolbar2QT | None = None,
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

        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        if not plotting_context.datasets():
            target.clear()
            target.canvas.draw()

        gs = self._figure.add_gridspec(2, 2)
        shared_axes = figure.add_subplot(gs[0])
        self._axes = [shared_axes]

        for databundle in plotting_context.datasets().values():
            dataset = databundle.dataset
            plotlabel = databundle.legend_label

            x_axis_labels = [dataset.x_axis_label(databundle.main_axis)]

            bins = dataset.x_axis(databundle.main_axis)

            if "angle" in plotlabel:
                axes = self._figure.add_subplot(
                    gs[2 + plotlabel.startswith("Azimuthal")]
                )

                axes.bar(
                    bins,
                    dataset.data[0, :],
                    linestyle="none",
                    label=plotlabel,
                    color=databundle.colour,
                    width=np.mean(np.diff(bins)),
                )
                axes.bar(
                    bins,
                    dataset.data[1, :],
                    linestyle=databundle.line_style,
                    label="Unique counts",
                    color="none",
                    edgecolor="black",
                    width=np.mean(np.diff(bins)),
                )
                self._axes.append(axes)
                axes.set_xlabel(", ".join(x_axis_labels))
                axes.set_title(dataset._name)
            elif "vs" in plotlabel:
                [curve] = shared_axes.plot(
                    bins,
                    dataset.data,
                    linestyle=databundle.line_style,
                    label=plotlabel,
                    color=databundle.colour,
                )
                try:
                    curve.set_marker(databundle.marker)
                except ValueError:
                    with contextlib.suppress(Exception):
                        curve.set_marker(int(databundle.marker))

                shared_axes.set_xlabel(", ".join(x_axis_labels))

            elif "in 3D" in plotlabel:
                axes = self._figure.add_subplot(gs[1], projection="3d")

                all_coords = np.concatenate(
                    [dataset.x_axis("q_x"), dataset.x_axis("q_y"), dataset.data]
                )
                self.axis3d_min = np.min(all_coords)
                self.axis3d_max = np.max(all_coords)

                axes.scatter(
                    dataset.x_axis("q_x"),
                    dataset.x_axis("q_y"),
                    dataset.data,
                    marker=databundle.marker,
                    label=plotlabel,
                    color=databundle.colour,
                )
                self._axes.append(axes)
                self.axes3d = axes
                axes.set_xlabel(dataset.x_axis_label("q_x"))
                axes.set_ylabel(dataset.x_axis_label("q_y"))
                axes.set_title(dataset._name)

        for axes in self._axes:
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

        for axes in self._axes:
            legend = axes.legend()
            legend.set_visible(plotting_context.use_legend)
            axes.grid(plotting_context.use_grid)
            axes.relim()
            axes.autoscale()

        self.axes3d.set_xlim([self.axis3d_min, self.axis3d_max])
        self.axes3d.set_ylim([self.axis3d_min, self.axis3d_max])
        self.axes3d.set_zlim([self.axis3d_min, self.axis3d_max])

        if self._toolbar is not None:
            self._toolbar.update()

        target.canvas.draw()
