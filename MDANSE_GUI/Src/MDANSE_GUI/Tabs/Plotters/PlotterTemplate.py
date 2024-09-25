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

from matplotlib.pyplot import style as mpl_style
from matplotlib import rcParams

from MDANSE.MLogging import LOG
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Units import measure

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class PlotterTemplate(metaclass=SubclassFactory):

    def __init__(self) -> None:
        self._figure = None
        self._axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None
        self._slider_reference = None
        self._plotting_context = None

    def collect_arrays(self):
        (
            self._datasets,
            self._colours,
            self._linestyles,
            self._markers,
            self._labels,
            self._names,
        ) = ({}, {}, {}, {}, {}, {})
        for name, databundle in self._plotting_context.datasets().items():
            dataset, colour, linestyle, marker, dataset_number, axis_label = databundle
            self._datasets[dataset_number] = dataset
            self._colours[dataset_number] = colour
            self._linestyles[dataset_number] = linestyle
            self._markers[dataset_number] = marker
            self._labels[dataset_number] = axis_label
            self._names[dataset_number] = name

    def convert_units(self):
        for dataset_number, dataset in self._datasets.items():
            axis_label = self._labels[dataset_number]
            try:
                best_unit, best_axis = (dataset._axes_units[axis_label], axis_label)
            except KeyError:
                best_unit, best_axis = dataset.longest_axis()
            plotlabel = dataset._labels["medium"]
            xaxis_unit = self._plotting_context.get_conversion_factor(best_unit)
            try:
                conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                    xaxis_unit
                )
            except:
                LOG.warning(f"Could not convert {best_unit} to {xaxis_unit}")
                conversion_factor = 1.0

    def plotting_workflow(self):
        self.collect_arrays()
        self.convert_units()
        self.apply_norms_and_weights()
        self.reset_figure()
        self.create_matplotlib_objects()
        self.apply_settings()
        self.apply_sliders()
        self.add_labels()
        self.save_settings()
        self.show_plot()

    def request_slider_values(self):
        if self._slider_reference is None:
            return
        self._slider_reference.collect_values()

    def clear(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> List[str]:
        return ["Slider 1", "Slider 2"]

    def slider_limits(self) -> List[str]:
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def sliders_coupled(self) -> bool:
        return False

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

    def apply_settings(self, plotting_context: "PlottingContext", colours=None):
        if colours is not None:
            self._current_colours = colours
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return
        try:
            matplotlib_style = colours["style"]
        except:
            pass
        else:
            if matplotlib_style is not None:
                mpl_style.use(matplotlib_style)
        try:
            bkg_col = colours["background"]
        except:
            pass
        else:
            if bkg_col is not None:
                for axes in self._axes:
                    axes.set_facecolor(bkg_col)
        try:
            col_seq = colours["curves"]
        except:
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

    def handle_slider(self, new_value: List[float]):
        self._slider_values = new_value

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "Figure" = None,
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
