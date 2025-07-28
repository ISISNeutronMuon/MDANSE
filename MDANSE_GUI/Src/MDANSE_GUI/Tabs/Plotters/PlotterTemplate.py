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

from typing import TYPE_CHECKING

from matplotlib import rcParams
from matplotlib.pyplot import style as mpl_style

from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.PlotModifiers.AxesWrapper import AxesWrapper
from MDANSE_GUI.Tabs.PlotModifiers.NormGenerator import NullNorms
from MDANSE_GUI.Tabs.PlotModifiers.WeightGenerator import NullWeights

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class PlotterTemplate(metaclass=SubclassFactory):
    def __init__(self) -> None:
        self._figure = None
        self._axes = {}
        self._unique_axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None
        self._slider_reference = None
        self._plotting_context = None
        self._weight_generator = NullWeights()
        self._norm_generator = NullNorms()

    def collect_arrays(self):
        (
            self._datasets,
            self._colours,
            self._linestyles,
            self._markers,
            self._labels,
            self._names,
            self._scale_factors,
        ) = ({}, {}, {}, {}, {}, {}, {})
        for name, databundle in self._plotting_context.datasets().items():
            (
                dataset,
                colour,
                linestyle,
                marker,
                dataset_number,
                axis_label,
                legend_label,
            ) = databundle
            self._datasets[dataset_number] = dataset
            self._colours[dataset_number] = colour
            self._linestyles[dataset_number] = linestyle
            self._markers[dataset_number] = marker
            self._labels[dataset_number] = axis_label
            self._names[dataset_number] = name
            self._scale_factors[dataset_number] = [1.0]

    def convert_units(self):
        for dataset_number, dataset in self._datasets:
            axis_label = self._labels[dataset_number]
            try:
                best_unit, best_axis = (dataset._axes_units[axis_label], axis_label)
            except KeyError:
                best_unit, best_axis = dataset.longest_axis()
            _plotlabel = dataset._labels["medium"]
            xaxis_unit = self._plotting_context.get_conversion_factor(best_unit)
            try:
                _conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                    xaxis_unit
                )
            except Exception:
                LOG.warning(f"Could not convert {best_unit} to {xaxis_unit}")
                _conversion_factor = 1.0

    def apply_weights(self):
        for dataset_number, dataset in self._datasets:
            try:
                scale_factor = self._weight_generator(dataset)
            except Exception:
                scale_factor = 1.0
            self._scale_factors[dataset_number].append([scale_factor])

    def apply_norms(self):
        for dataset_number, dataset in self._datasets.items():
            try:
                scale_factor = self._norm_generator(dataset)
            except Exception:
                scale_factor = 1.0
            self._scale_factors[dataset_number].append([scale_factor])

    def reset_figure(self, figure=None, toolbar=None):
        self.enable_slider(False)
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self._figure = target

    def create_plots(self):
        axes = self._figure.add_subplot(111)
        wrapper = AxesWrapper(axes)
        self._unique_axes.append(wrapper)
        for dataset_number, dataset in self._datasets.items():
            self._axes[dataset_number] = wrapper

    def populate_plots(self):
        for dataset_number, dataset in self._datasets.items():
            wrapper = self._axes[dataset_number]
            wrapper.axes.plot(dataset)  # We need to think how to pass information here

    def add_labels(self):
        for wrapper in self._unique_axes:
            wrapper.axes.set_title("MDANSE plot")
            wrapper.axes.grid(True)
            wrapper.axes.legend(loc=0)

    def show_plot(self):
        pass

    def apply_sliders(self):
        slider_values = self._slider_reference._current_values
        self.handle_slider(slider_values)

    def save_settings(self):
        pass

    def plotting_workflow(self):
        self.collect_arrays()
        self.convert_units()
        self.apply_weights()
        self.apply_norms()
        self.reset_figure()
        self.create_plots()
        self.populate_plots()
        self.add_labels()
        self.show_plot()
        self.apply_sliders()
        self.save_settings()

    def request_slider_values(self):
        if self._slider_reference is None:
            return
        self._slider_reference.collect_values()

    def clear(self, figure: Figure = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> list[str]:
        return ["Slider 1", "Slider 2"]

    def slider_limits(self) -> list[str]:
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def sliders_coupled(self) -> bool:
        return False

    def get_figure(self, figure: Figure = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def apply_settings(self, plotting_context: PlottingContext, colours=None):
        if colours is not None:
            self._current_colours = colours
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        try:
            matplotlib_style = colours["style"]
        except Exception:
            pass
        else:
            if matplotlib_style is not None:
                mpl_style.use(matplotlib_style)
        try:
            bkg_col = colours["background"]
        except Exception:
            pass
        else:
            if bkg_col is not None:
                for axes in self._axes:
                    axes.set_facecolor(bkg_col)
        try:
            col_seq = colours["curves"]
        except Exception:
            pass
        else:
            if col_seq is not None:
                for axes in self._axes:
                    axes.set_prop_cycle("color", col_seq)

    def enable_slider(self, allow_slider: bool = True):
        if allow_slider:
            self._slider_reference.setEnabled(True)
            self._slider_reference.blockSignals(False)
        else:
            self._slider_reference.setEnabled(False)
            self._slider_reference.blockSignals(True)

    def handle_slider(self, new_value: list[float]):
        self._slider_values = new_value

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure = None,
        update_only=False,
        toolbar=None,
    ):
        self._plotting_context = plotting_context
        target = self.get_figure(figure)
        if target is None:
            return
        self._target_figure = target
        if toolbar is not None:
            self._toolbar = toolbar
        axes = target.add_subplot(111)
        temp = AxesWrapper(axes)
        self._axes = [temp]
        self.apply_settings(plotting_context)
