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

import math
from typing import TYPE_CHECKING, Any

import numpy as np
from matplotlib.pyplot import colorbar as mpl_colorbar
from scipy.interpolate import interp1d

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Heatmap(Plotter):
    """Creates a 2D heatmap plot."""

    def __init__(self) -> None:
        """Initialise all plotting parameters to defaults."""
        super().__init__()
        self._figure = None
        self._backup_images = {}
        self._backup_arrays = {}
        self._backup_minmax = {}
        self._backup_scale_interpolators = {}
        self._current_x_axes = []
        self._backup_limits = {}
        self._initial_values = [0.0, 100.0]
        self._slider_values = [0.0, 100.0]
        self._last_minmax = [-1, -1]
        self._slice_axis = 2
        self._plot_limit = 1

    def clear(self, figure: Figure = None):
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

    def get_figure(self, figure: Figure = None):
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
        for ds_num, image in self._backup_images.items():
            data = self._backup_arrays[ds_num]
            new_data = self.normalise_array(data)
            image.set_data(new_data)
            percentiles = np.linspace(0, 100.0, 21)
            results = [np.percentile(new_data, perc) for perc in percentiles]
            self._backup_scale_interpolators[ds_num] = interp1d(
                percentiles,
                results,
            )
        self.request_slider_values()

    def handle_slider(self, new_value: list[float]):
        """Adjust colormap values based on slider values."""
        super().handle_slider(new_value)
        target = self._figure
        if target is None:
            return
        if new_value[1] <= new_value[0]:
            return
        self._slider_values = [new_value[0], new_value[1]]
        for ds_num, image in self._backup_images.items():
            try:
                last_minmax = self._backup_minmax[ds_num]
            except KeyError:
                self._backup_minmax[ds_num] = [-1, -1]
                last_minmax = [-1, -1]
            interpolator = self._backup_scale_interpolators[ds_num]
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
                    image.set_clim([newmin, newmax])
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {newmin}, {newmax}"
                    )
                else:
                    self._figure.canvas.draw_idle()
                    self._backup_minmax[ds_num] = [newmin, newmax]
        target.canvas.draw()

    def check_curve_lengths(self):
        """Find the maximum number of elements in the x axes of the plot data."""
        self.curve_length_limit = 0
        for xdata in self._current_x_axes:
            self.curve_length_limit = max(self.curve_length_limit, len(xdata))

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure = None,
        update_only=False,
        toolbar=None,
    ):
        """Plot the first dataset as a heatmap.

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
        self.enable_slider(allow_slider=True)
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self._figure = target
        self._current_x_axes = []
        self._normalisation_errors = []
        self._backup_images = {}
        self._backup_arrays = {}
        self._backup_scale_interpolators = {}
        self._axes = []
        self.apply_settings(plotting_context)
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        nplots = 0
        for ds_index, databundle in enumerate(plotting_context.datasets().values()):
            if nplots >= self._plot_limit:
                break
            ds = databundle.dataset
            if ds._n_dim == 1:
                continue
            elif ds._n_dim == 3:
                replacement_axis_number = None
                for number, axis_name in enumerate(ds._axes.keys()):
                    if axis_name == databundle.main_axis:
                        replacement_axis_number = number
                if replacement_axis_number is None:
                    ds.planes_vs_axis(self._slice_axis, max_limit=self._plot_limit)
                else:
                    ds.planes_vs_axis(
                        replacement_axis_number, max_limit=self._plot_limit
                    )
                nplots += len(ds._planes)
            else:
                nplots += 1
            try:
                self._backup_scale_interpolators[databundle.row](51.2)
            except Exception:
                percentiles = np.linspace(0, 100.0, 21)
                results = [np.percentile(ds._data, perc) for perc in percentiles]
                self._backup_scale_interpolators[databundle.row] = interp1d(
                    percentiles,
                    results,
                )
        nplots = min(nplots, self._plot_limit)
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for ds_index, databundle in enumerate(plotting_context.datasets().values()):
            if ds_index >= self._plot_limit:
                break
            dataset = databundle.dataset
            transposed = False
            primary_axis_number = 0
            limits = []
            x_axis_labels, y_axis_labels = [], []
            for number, axis_name in enumerate(ds._axes.keys()):
                if axis_name == databundle.main_axis:
                    primary_axis_number = number
            if dataset._n_dim == 1:
                continue
            if dataset._n_dim == 3:
                all_numbers, all_datasets = (
                    list(dataset._planes.keys()),
                    list(dataset._planes.values()),
                )
                all_labels = [dataset._plane_labels[number] for number in all_numbers]
                for counter, name in enumerate(dataset._axes.keys()):
                    if counter == primary_axis_number:
                        continue
                    axis_array = dataset.x_axis(name)
                    limits += [
                        axis_array[0],
                        axis_array[-1],
                    ]
                    if not x_axis_labels:
                        x_axis_labels.append(dataset.x_axis_label(name))
                        self._current_x_axes.append(axis_array)
                    else:
                        y_axis_labels.append(dataset.x_axis_label(name))
            else:
                all_numbers = [0]
                if primary_axis_number == 0:
                    all_datasets = [dataset._data.T]
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
            self._backup_arrays[databundle.row] = np.nan_to_num(
                all_datasets[xnum][::-1, :]
            )
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
                    dataset._data.min(),
                    dataset._data.max(),
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
            if plotting_context.use_legend:
                axes.legend()
            axes.grid(plotting_context.use_grid)
        self.check_curve_lengths()
        self.request_slider_values()
        target.canvas.draw()
