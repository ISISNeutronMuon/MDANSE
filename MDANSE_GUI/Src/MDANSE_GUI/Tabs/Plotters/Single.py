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

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Single(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._curve_limit_per_dataset = 12
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

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

    def slider_labels(self) -> List[str]:
        return ["Y offset", "X offset"]

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def handle_slider(self, new_value: List[float]):
        super().handle_slider(new_value)
        self.offset_curves()

    def offset_curves(self):
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
        self._axes[0].set_xlim(saved_xmin, saved_xmax)
        self._axes[0].set_ylim(saved_ymin, saved_ymax)
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
        xaxis_unit = None
        self._active_curves = []
        self._backup_curves = []
        self.get_mpl_colors()
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context, colours)
        self.height_max, self.length_max = 0.0, 0.0
        if plotting_context.set_axes() is None:
            LOG.error("Axis check failed.")
            return
        for name, databundle in plotting_context.datasets().items():
            dataset, colour, linestyle, marker, _ = databundle
            best_unit, best_axis = dataset.longest_axis()
            plotlabel = dataset._labels["medium"]
            xaxis_unit = plotting_context.get_conversion_factor(best_unit)
            try:
                conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                    xaxis_unit
                )
            except:
                continue
            else:
                if dataset._n_dim == 1:
                    [temp] = axes.plot(
                        dataset._axes[best_axis] * conversion_factor,
                        dataset._data,
                        linestyle=linestyle,
                        label=plotlabel,
                        color=colour,
                    )
                    try:
                        temp.set_marker(marker)
                    except ValueError:
                        try:
                            temp.set_marker(int(marker))
                        except:
                            pass
                    self._active_curves.append(temp)
                    self._backup_curves.append([temp.get_xdata(), temp.get_ydata()])
                    self.height_max = max(self.height_max, temp.get_ydata().max())
                    self.length_max = max(self.length_max, temp.get_xdata().max())
                else:
                    multi_curves = dataset.curves_vs_axis(best_unit)
                    counter = 0
                    for key, value in multi_curves.items():
                        counter += 1
                        if counter >= self._curve_limit_per_dataset:
                            break
                        try:
                            [temp] = axes.plot(
                                dataset._axes[best_axis] * conversion_factor,
                                value,
                                label=plotlabel + ":" + dataset._curve_labels[key],
                            )
                            self._active_curves.append(temp)
                            self._backup_curves.append(
                                [temp.get_xdata(), temp.get_ydata()]
                            )
                            self.height_max = max(
                                self.height_max, temp.get_ydata().max()
                            )
                            self.length_max = max(
                                self.length_max, temp.get_xdata().max()
                            )
                        except ValueError:
                            LOG.error(
                                f"Plotting failed for {plotlabel} using {best_axis}"
                            )
                            LOG.error(f"x_axis={dataset._axes[best_axis]}")
                            LOG.error(f"values={value}")
                            return
        if update_only:
            axes.set_xlim((self._backup_limits[0], self._backup_limits[1]))
            axes.set_ylim((self._backup_limits[2], self._backup_limits[3]))
        else:
            xlimits, ylimits = axes.get_xlim(), axes.get_ylim()
            self._backup_limits = [xlimits[0], xlimits[1], ylimits[0], ylimits[1]]
        if xaxis_unit is not None:
            axes.set_xlabel(xaxis_unit)
        axes.grid(True)
        axes.legend(loc=0)
        self.offset_curves()
