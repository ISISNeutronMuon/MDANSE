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

import csv
import math
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import islice
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO

import numpy as np
from matplotlib.axes import Axes
from matplotlib.image import AxesImage
from matplotlib.pyplot import colorbar as mpl_colorbar
from more_itertools import ilen
from scipy.interpolate import interp1d

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure
    from matplotlib.image import AxesImage

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


@Plotter.register("Heatmap")
class Heatmap(Plotter):
    """Creates a 2D heatmap plot."""

    @dataclass
    class BackupInfo:
        ind: int
        image: AxesImage
        array: np.ndarray
        minmax: tuple[float, float]
        limits: tuple[float, float, float, float]
        interp: interp1d

    def __init__(self) -> None:
        """Initialise all plotting parameters to defaults."""
        super().__init__()
        self._figure = None
        self._backup: dict[int, Heatmap.BackupInfo] = {}
        self._current_x_axes = []
        self._initial_values = [0.0, 100.0]
        self._slider_values = [0.0, 100.0]
        self._slice_axis = 2
        self._plot_limit = 9

    def clear(self, figure: Figure | None = None):
        """Clear the figure."""
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> list[str]:
        """Return labels for the sliders in heatmap mode."""
        return ["Minimum (percentile)", "Maximum (percentile)"]

    def slider_limits(self) -> list[str]:
        """Return slider limits for the colormap, in percent."""
        return self._number_of_sliders * [[0.0, 100.0, 0.01]]

    def sliders_coupled(self) -> bool:
        """Confirm that sliders are coupled in heatmap mode."""
        return True

    def get_figure(self, figure: Figure | None = None):
        """Return current figure which will be used for plotting."""
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
        for backup in self._backup.values():
            data = backup.array
            new_data = self.normalise_array(data)
            backup.image.set_data(new_data)
            percentiles = np.linspace(0, 100.0, 21)
            results = np.percentile(np.nan_to_num(new_data), percentiles)
            self._backup_scale_interpolators[ds_num] = interp1d(
                percentiles,
                results,
            )
        self.request_slider_values()

    def handle_slider(self, new_value: list[float]):
        """Adjust colormap values based on slider values."""
        super().handle_slider(new_value)
        target = self._figure

        if target is None or new_value[1] <= new_value[0]:
            return

        self._slider_values = [new_value[0], new_value[1]]

        for backup in self._backup.values():
            try:
                last_minmax = backup.minmax
            except KeyError:
                backup.minmax = (-1, -1)
                last_minmax = [-1, -1]

            interpolator = backup.interp
            newmax = interpolator(new_value[1])
            newmin = interpolator(new_value[0])

            if newmax < newmin:
                if newmax == last_minmax[1]:
                    newmin = float(newmax)
                else:
                    newmax = float(newmin)
            if newmin == last_minmax[0] and newmax == last_minmax[1]:
                return
            if newmax >= newmin:
                try:
                    backup.image.set_clim([newmin, newmax])
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {newmin}, {newmax}"
                    )
                else:
                    self._figure.canvas.draw_idle()
                    backup.minmax = [newmin, newmax]
        target.canvas.draw()

    def check_curve_lengths(self):
        """Find the maximum number of elements in the x axes of the plot data."""
        self.curve_length_limit = max(map(len, self._current_x_axes), default=0)

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure | None = None,
        update_only: bool = False,
        toolbar: Toolbar | None = None,
    ):
        """Plot the first dataset as a heatmap.

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
        self.enable_slider(allow_slider=True)
        target = self.get_figure(figure)
        if target is None:
            return

        if toolbar is not None:
            self._toolbar = toolbar

        self._figure = target
        self._figure.set_layout_engine(layout="constrained")
        self._current_x_axes = []
        minmax_bak = {key: val.minmax for key, val in self._backup.items()}
        scale_interpolators = {val.ind: val.interp for val in self._backup.values()}
        self._backup = {}
        self._axes = []

        self.apply_settings(plotting_context)
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        nplots = min(ilen(plotting_context.planes(self._slice_axis)), self._plot_limit)

        if not nplots:
            self.plot_blank()
            return

        # Check interpolators
        for databundle in plotting_context.datasets().values():
            try:
                scale_interpolators[databundle.row](51.2)
            except Exception:
                percentiles = np.linspace(0, 100.0, 21)
                results = [
                    np.percentile(np.nan_to_num(ds._data), perc) for perc in percentiles
                ]
                self._backup_scale_interpolators[databundle.row] = interp1d(
                    percentiles,
                    results,
                )

        grid_size = self.grid_size(nplots)
        gs = self._figure.add_gridspec(*grid_size)

        for ind, (databundle, label, plane) in enumerate(
            islice(plotting_context.planes(self._slice_axis), self._plot_limit),
        ):
            dataset = databundle.dataset
            limits = []
            x_axis_labels, y_axis_labels = [], []

            for name in dataset._axes:
                axis_array = dataset.x_axis(name)
                limits += [axis_array[0], axis_array[-1]]
                if not x_axis_labels:
                    x_axis_labels.append(dataset.x_axis_label(name))
                    self._current_x_axes.append(axis_array)
                else:
                    all_datasets = [dataset._data]
                    transposed = True
                all_labels = [dataset._name]
                for counter, name in enumerate(dataset._axes.keys()):
                    axis_array = dataset.x_axis(name)
                    limits += [
                        axis_array[0],
                        axis_array[-1],
                    ]
                    if counter == primary_axis_number:
                        x_axis_labels.append(dataset.x_axis_label(name))
                        self._current_x_axes.append(axis_array)
                    else:
                        y_axis_labels.append(dataset.x_axis_label(name))
            if transposed:
                limits = limits[2:] + limits[:2]
            for xnum in range(len(all_datasets)):
                if startnum > self._plot_limit:
                    LOG.warning(
                        "Datasets above the current limit of %s will be ignored",
                        self._plot_limit,
                    )
                    break
                axes = target.add_subplot(gridsize, gridsize, startnum)
                startnum += 1
                self._axes.append(axes)
                image = axes.imshow(
                    all_datasets[xnum][::-1, :],
                    extent=limits,
                    aspect="auto",
                    interpolation=None,
                    cmap=plotting_context.colormap,
                )
                axes.set_title(all_labels[xnum])
                colorbar = mpl_colorbar(image, ax=image.axes, format="%.1e", pad=0.02)
                colorbar.set_label(dataset._data_unit)
                xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
            self._backup_arrays[databundle.row] = all_datasets[xnum][::-1, :]
            if update_only:
                interpolator = self._backup_scale_interpolators[databundle.row]
                last_minmax = [
                    interpolator(self._slider_values[0]),
                    interpolator(self._slider_values[1]),
                ]
                try:
                    image.set_clim(last_minmax)
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {last_minmax}",
                    )
                self._backup_limits[databundle.row] = [
                    xlimits[0],
                    xlimits[1],
                    ylimits[0],
                    ylimits[1],
                ]
                xlim = axes.get_xlim()
                self._backup_limits[databundle.row][0] = xlim[0]
                self._backup_limits[databundle.row][1] = xlim[1]
                ylim = axes.get_ylim()
                self._backup_limits[databundle.row][2] = ylim[0]
                self._backup_limits[databundle.row][3] = ylim[1]
            else:
                self._backup_limits[databundle.row] = [
                    xlimits[0],
                    xlimits[1],
                    ylimits[0],
                    ylimits[1],
                ]
                interpolator = self._backup_scale_interpolators[databundle.row]
                last_minmax = [
                    interpolator(self._slider_values[0]),
                    interpolator(self._slider_values[1]),
                ]
                try:
                    image.set_clim(last_minmax)
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {last_minmax}",
                    )
                self._backup_minmax[databundle.row] = [
                    np.nanmin(dataset._data),
                    np.nanmax(dataset._data),
                ]
                self._backup_limits[databundle.row] = [
                    xlimits[0],
                    xlimits[1],
                    ylimits[0],
                    ylimits[1],
                ]
            axes.set_xlabel(", ".join(np.unique(x_axis_labels)))
            axes.set_ylabel(", ".join(np.unique(y_axis_labels)))
            self._backup_images[databundle.row] = image
        if startnum > 1:
            legend = axes.legend()
            legend.set_visible(plotting_context.use_legend)
            axes.grid(plotting_context.use_grid)

        if nplots == 1:  # Exploit label from loop for one plot
            self._figure.suptitle(label)

        self.check_curve_lengths()
        self.request_slider_values()
        target.canvas.draw()

    @staticmethod
    def _write_save_data(
        file: TextIO, axis: Axes, line: AxesImage, ax_ind: int, line_ind: int
    ) -> None:
        """Write structured save data to csv file.

        Parameters
        ----------
        file : TextIO
            File to write to.
        axis : Axes
            Axis to write.
        line : AxesImage
            Heatmap to write.
        ax_ind : int
            Index of axis.
        line_ind : int
            Index of line (always 1).
        """
        title = axis.get_title() or ax_ind
        line_label = line.get_label() or line_ind
        xlabel = axis.get_xlabel()
        ylabel = axis.get_ylabel()

        writer = csv.writer(file)
        eol = writer.dialect.lineterminator
        file.write(f"# Axis: {title}; Line: {line_label or line_ind}{eol}")

        data = line.get_array().T
        extent = line.get_extent()

        x, y = (
            np.linspace(start, stop, n)
            for (start, stop), n in zip(
                (extent[:2], extent[2:]),
                data.shape,
                strict=True,
            )
        )

        writer.writerow((xlabel or "index", ylabel or "value", "data"))
        for (i, j), dat in np.ndenumerate(data):
            writer.writerow((x[i], y[j], dat))

        file.write(eol)

    @staticmethod
    def _get_datasets(axis: Axes) -> Iterator[AxesImage]:
        """Yield datasets from axis.

        Parameters
        ----------
        axis : Axes
            Axis to use.

        Yields
        ------
        AxesImage
            Each image in dataset.
        """
        yield from axis.get_images()
