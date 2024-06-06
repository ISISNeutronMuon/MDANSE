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

from matplotlib.pyplot import colorbar as mpl_colorbar

from MDANSE.Framework.Units import measure
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Heatmap(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> List[str]:
        return ["Minimum", "Maximum"]

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[0.0, 1.0, 0.01]]

    def get_figure(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            print(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def plot(
        self, plotting_context: "PlottingContext", figure: "Figure" = None, colours=None
    ):
        target = self.get_figure(figure)
        if target is None:
            return
        xaxis_unit = None
        yaxis_unit = None
        self.get_mpl_colors()
        self._axes = []
        self.apply_settings(plotting_context, colours)
        if plotting_context.set_axes() is None:
            print("Axis check failed.")
            return
        nplots = 0
        for databundle in plotting_context.datasets().values():
            ds, _, _ = databundle
            if ds._n_dim == 1:
                continue
            nplots += 1
        gridsize = int(math.ceil(nplots**0.5))
        startnum = 1
        for name, databundle in plotting_context.datasets().items():
            dataset, _, _ = databundle
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
                cmap=plotting_context._colour_map,
            )
            colorbar = mpl_colorbar(image, ax=image.axes, format="%.1e", pad=0.02)
            colorbar.set_label(dataset._data_unit)
            axes.set_xlabel(axis_units[0])
            axes.set_ylabel(axis_units[1])
        # axes.grid(True)
        target.canvas.draw()
