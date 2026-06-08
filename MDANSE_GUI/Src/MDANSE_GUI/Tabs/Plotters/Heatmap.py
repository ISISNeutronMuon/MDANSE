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
from dataclasses import dataclass, field
from itertools import islice
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO

import numpy as np
from matplotlib.axes import Axes
from matplotlib.pyplot import colorbar as mpl_colorbar
from more_itertools import ilen, nth
from scipy.interpolate import interp1d

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Models.PlottingContext import PlotArgs
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar
    from matplotlib.figure import Figure
    from matplotlib.image import AxesImage

    from MDANSE.util_types import FloatArray
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


@Plotter.register("Heatmap")
class Heatmap(Plotter):
    """Creates a 2D heatmap plot."""

    @dataclass
    class BackupInfo:
        ind: int
        image: AxesImage = None
        array: FloatArray = field(default_factory=lambda: np.empty((0,), dtype=float))
        minmax: tuple[float, float] = (-np.inf, np.inf)
        limits: tuple[float, float, float, float] = (-np.inf, np.inf, -np.inf, np.inf)
        interp: interp1d = None
        title: str = ""

    def __init__(self) -> None:
        """Initialise all plotting parameters to defaults."""
        super().__init__()
        self._figure = None
        self._axes_titles: list[str] = []
        self._backup: dict[str, Heatmap.BackupInfo] = {}
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

    def slider_limits(self) -> list[tuple[float, float, float]]:
        """Return slider limits for the colormap, in percent."""
        return [(0.0, 100.0, 0.01)] * self._number_of_sliders

    def sliders_coupled(self) -> bool:
        """Confirm that sliders are coupled in heatmap mode."""
        return True

    def get_figure(self, figure: Figure | None = None) -> Figure | None:
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
            backup.interp = interp1d(percentiles, results)

        self.request_slider_values()

    def handle_slider(self, new_value: list[float]):
        """Adjust colormap values based on slider values."""
        super().handle_slider(new_value)

        if self._figure is None or new_value[1] <= new_value[0]:
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
                    backup.image.set_clim((newmin, newmax))
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {newmin}, {newmax}"
                    )
                else:
                    self._figure.canvas.draw_idle()
                    backup.minmax = (newmin, newmax)
        self._figure.canvas.draw()

    def toggle_legend(self, enabled: bool) -> None:
        if self._figure is None:
            return

        for axes, title in zip(self._axes, self._axes_titles, strict=True):
            axes.set_title(
                title if enabled else "",
                fontsize=self.title_fontsize(title),
            )

        self._figure.canvas.draw()

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

        scale_interpolators = {val.ind: val.interp for val in self._backup.values()}

        self._backup.clear()
        self._axes.clear()
        self._axes_titles.clear()

        self.apply_settings(plotting_context)
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

        self._n_curves = min(
            ilen(plotting_context.planes(self._slice_axis)), self._plot_limit
        )

        if not self.n_curves:
            self.plot_blank()
            return

        def get_interp(ind: int, data: FloatArray):
            # Check interpolators
            try:
                scale_interpolators[ind](51.2)
            except Exception:
                percentiles = np.linspace(0, 100.0, 21)
                results = [
                    np.percentile(np.nan_to_num(data), perc) for perc in percentiles
                ]
                return interp1d(percentiles, results)
            else:
                return scale_interpolators[ind]

        grid_size = self.grid_size(self.n_curves)
        gs = self._figure.add_gridspec(*grid_size)

        for ind, (databundle, label, plane, axis_labels) in enumerate(
            islice(plotting_context.planes(self._slice_axis), self._plot_limit),
        ):
            self._backup[label] = Heatmap.BackupInfo(ind=ind)
            dataset = databundle.dataset

            axes = self._figure.add_subplot(gs[ind])

            image = self._plot_single(
                axes,
                plane[:, ::-1].T,
                databundle,
                label=label,
                axis_labels=axis_labels,
                colour=plotting_context.colormap,
            )

            xlimits, ylimits = axes.get_xlim(), axes.get_ylim()

            self._backup[label].interp = get_interp(ind, plane)

            last_minmax = (
                self._backup[label].interp(self._slider_values[0]),
                self._backup[label].interp(self._slider_values[1]),
            )

            try:
                image.set_clim(last_minmax)
            except ValueError:
                LOG.error(
                    f"Matplotlib could not set colorbar limits to {last_minmax}",
                )

            if update_only:
                self._backup[label].limits = (*xlimits, *ylimits)
            else:
                self._backup[label].minmax = (
                    np.nanmin(dataset._data),
                    np.nanmax(dataset._data),
                )
                self._backup[label].limits = (*xlimits, *ylimits)

        self.toggle_legend(plotting_context.use_legend)
        self.toggle_grid(plotting_context.use_grid)

        if self.n_curves == 1:  # Exploit label from loop for one plot
            self._figure.suptitle(label)

        self.check_curve_lengths()
        self.request_slider_values()
        self._figure.canvas.draw()

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

    def _plot_single(
        self,
        axes: Axes,
        plane: FloatArray,
        databundle: PlotArgs,
        *,
        label: str,
        axis_labels: tuple[str, str],
        colour: str,
    ) -> AxesImage:
        dataset = databundle.dataset

        x_label, y_label = axis_labels

        x_axis = dataset.x_axis(x_label)
        y_axis = dataset.x_axis(y_label)

        limits = (x_axis[0], x_axis[-1], y_axis[0], y_axis[-1])
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)

        image = axes.imshow(
            plane,
            extent=limits,
            aspect="auto",
            interpolation=None,
            cmap=colour,
        )

        colorbar = mpl_colorbar(image, ax=image.axes, format="%.1e", pad=0.02)
        colorbar.set_label(dataset._data_unit)

        self._axes.append(axes)
        self._axes_titles.append(label)
        self._backup[label].array = plane
        self._backup[label].image = image

        return image
