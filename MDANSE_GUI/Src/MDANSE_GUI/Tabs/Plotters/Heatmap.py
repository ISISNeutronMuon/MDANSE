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
from typing import TYPE_CHECKING, List
import math

import numpy as np
from scipy.interpolate import interp1d
from matplotlib.pyplot import colorbar as mpl_colorbar

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Heatmap(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._backup_images = {}
        self._backup_arrays = {}
        self._backup_minmax = {}
        self._backup_scale_interpolators = {}
        self._backup_limits = {}
        self._last_axes_units = {}
        self._initial_values = [0.0, 100.0]
        self._slider_values = [0.0, 100.0]
        self._last_minmax = [-1, -1]

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> List[str]:
        return ["Minimum (percentile)", "Maximum (percentile)"]

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[0.0, 100.0, 0.1]]

    def sliders_coupled(self) -> bool:
        return True

    def get_figure(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def handle_slider(self, new_value: List[float]):
        super().handle_slider(new_value)
        target = self._figure
        if target is None:
            return
        if new_value[1] <= new_value[0]:
            return
        else:
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

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "Figure" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self._figure = target
        self._backup_images = {}
        self._backup_arrays = {}
        self._backup_scale_interpolators = {}
        xaxis_unit = None
        yaxis_unit = None
        self.get_mpl_colors()
        self._axes = []
        if not update_only:
            self._last_axes_units = {}
        self.apply_settings(plotting_context, colours)
        if plotting_context.set_axes() is None:
            LOG.error("Axis check failed.")
            return
        nplots = 0
        for databundle in plotting_context.datasets().values():
            ds, _, _, _, ds_num = databundle
            if ds._n_dim == 1:
                continue
            nplots += 1
            try:
                self._backup_scale_interpolators[ds_num](51.2)
            except:
                percentiles = np.linspace(0, 100.0, 21)
                results = [np.percentile(ds._data, perc) for perc in percentiles]
                self._backup_scale_interpolators[ds_num] = interp1d(
                    percentiles, results
                )
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for num, databundle in enumerate(plotting_context.datasets().values()):
            dataset, _, _, _, ds_num = databundle
            if dataset._n_dim == 1:
                continue
            axes = target.add_subplot(gridsize, gridsize, startnum)
            startnum += 1
            self._axes.append(axes)
            limits = []
            axis_units = []
            for key, value in dataset._axes_units.items():
                target_unit = plotting_context.get_conversion_factor(value)
                axis_array = dataset._axes[key]
                try:
                    conversion_factor = measure(1.0, value, equivalent=True).toval(
                        target_unit
                    )
                except:
                    limits += [axis_array[0], axis_array[-1]]
                    axis_units.append(value)
                else:
                    limits += [
                        axis_array[0] * conversion_factor,
                        axis_array[-1] * conversion_factor,
                    ]
                    axis_units.append(target_unit)
            image = axes.imshow(
                dataset._data.T[::-1, :],
                extent=limits,
                aspect="auto",
                interpolation=None,
                cmap=plotting_context.colormap,
            )
            colorbar = mpl_colorbar(image, ax=image.axes, format="%.1e", pad=0.02)
            colorbar.set_label(dataset._data_unit)
            xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
            self._backup_arrays[ds_num] = np.nan_to_num(dataset._data)
            if update_only:
                interpolator = self._backup_scale_interpolators[ds_num]
                last_minmax = [
                    interpolator(self._slider_values[0]),
                    interpolator(self._slider_values[1]),
                ]
                try:
                    image.set_clim(last_minmax)
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {last_minmax}"
                    )
                try:
                    last_limits = self._backup_limits[ds_num]
                except KeyError:
                    self._backup_limits[ds_num] = [
                        xlimits[0],
                        xlimits[1],
                        ylimits[0],
                        ylimits[1],
                    ]
                    last_limits = self._backup_limits[ds_num]
                else:
                    try:
                        previous_units = self._last_axes_units[ds_num]
                    except KeyError:
                        self._last_axes_units[ds_num] = [axis_units[0], axis_units[1]]
                        previous_units = self._last_axes_units[ds_num]
                    if axis_units[0] == previous_units[0]:
                        try:
                            axes.set_xlim((last_limits[0], last_limits[1]))
                        except ValueError:
                            LOG.error(
                                f"Matplotlib could not set x limits to {last_limits[0]}, {last_limits[1]}"
                            )
                    else:
                        self._last_axes_units[ds_num][0] = axis_units[0]
                        xlim = axes.get_xlim()
                        self._backup_limits[ds_num][0] = xlim[0]
                        self._backup_limits[ds_num][1] = xlim[1]
                    if axis_units[1] == previous_units[1]:
                        try:
                            axes.set_ylim((last_limits[2], last_limits[3]))
                        except ValueError:
                            LOG.error(
                                f"Matplotlib could not set x limits to {last_limits[2]}, {last_limits[3]}"
                            )
                    else:
                        self._last_axes_units[ds_num][1] = axis_units[1]
                        ylim = axes.get_ylim()
                        self._backup_limits[ds_num][2] = ylim[0]
                        self._backup_limits[ds_num][3] = ylim[1]
            else:
                try:
                    last_limits = self._backup_limits[ds_num]
                except KeyError:
                    self._backup_limits[ds_num] = [
                        xlimits[0],
                        xlimits[1],
                        ylimits[0],
                        ylimits[1],
                    ]
                    last_limits = self._backup_limits[ds_num]
                interpolator = self._backup_scale_interpolators[ds_num]
                last_minmax = [
                    interpolator(self._slider_values[0]),
                    interpolator(self._slider_values[1]),
                ]
                try:
                    image.set_clim(last_minmax)
                except ValueError:
                    LOG.error(
                        f"Matplotlib could not set colorbar limits to {last_minmax}"
                    )
                self._backup_minmax[ds_num] = [dataset._data.min(), dataset._data.max()]
                self._backup_limits[ds_num] = [
                    xlimits[0],
                    xlimits[1],
                    ylimits[0],
                    ylimits[1],
                ]
                self._last_axes_units[ds_num] = axis_units
            axes.set_xlabel(axis_units[0])
            axes.set_ylabel(axis_units[1])
            self._backup_images[ds_num] = image
        # axes.grid(True)
        self.request_slider_values()
        target.canvas.draw()
