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

if TYPE_CHECKING:
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext

import matplotlib.pyplot as mpl
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter
from MDANSE_GUI.Widgets.NormalisationWidget import NormalisationWidget
from MDANSE_GUI.Widgets.RestrictedSlider import RestrictedSlider


class SliderPack(QWidget):
    """Widget combining several RestrictedSlider instances."""

    new_values = Signal(object)

    def __init__(self, *args, n_sliders=2, **kwargs) -> None:
        """Create the widget with the specified number of sliders."""
        super().__init__(*args, **kwargs)
        layout = QGridLayout(self)
        self.setLayout(layout)
        self._labels = []
        self._sliders = []
        self._spinboxes = []
        self._current_values = []
        self._minarray = np.zeros(n_sliders)
        self._maxarray = np.ones(n_sliders)
        self._valarray = np.ones(n_sliders) * 0.5
        self._steparray = np.ones(n_sliders) * 0.01
        self._clickarray = np.array(n_sliders * [101], dtype=int)
        current_row = 0
        for n in range(n_sliders):
            label = QLabel(self)
            slider = RestrictedSlider(self)
            slider.setOrientation(Qt.Orientation.Horizontal)
            box = QDoubleSpinBox(self)
            box.setSingleStep(self._steparray[n])
            layout.addWidget(label, current_row, 0)
            layout.addWidget(slider, current_row, 1, 1, 2)
            layout.addWidget(box, current_row, 3)
            current_row += 1
            self._labels.append(label)
            self._sliders.append(slider)
            self._spinboxes.append(box)
            slider.valueChanged.connect(self.slider_to_box)
            box.valueChanged.connect(self.box_to_slider)
            box.valueChanged.connect(self.collect_values)
            self._current_values.append(0)
        slider1 = self._sliders[0]
        slider2 = self._sliders[1]
        slider1.new_limit.connect(slider2.set_lower_limit)
        slider2.new_limit.connect(slider1.set_upper_limit)

    @Slot(bool)
    def new_coupling(self, new_val: bool):
        """Couples the first two sliders together if new_val is true.

        Parameters
        ----------
        new_val : bool
            True for coupled sliders, false otherwise

        """
        self._sliders[0]._coupled = new_val
        self._sliders[1]._coupled = new_val

    @Slot(object)
    def new_slider_labels(self, input_labels: list[str]):
        """Change the text labels of the sliders to new values."""
        for number, element in enumerate(input_labels):
            self._labels[number].setText(element)

    @Slot(object)
    def new_limits(self, input_limits: list[list[float]]):
        """Change the limits and step number of the sliders.

        Since QSlider works with integer numbers, the float
        values of limits are used in the spin boxes, while
        the sliders work with integer 'clicks' in the background.

        Parameters
        ----------
        input_limits : list[list[float]]
            For each slider, [minimum, maximum, step_size] values

        """
        for number, element in enumerate(input_limits):
            minimum, maximum, stepsize = element[0], element[1], element[2]
            clicks = int(round((maximum - minimum) / stepsize))
            self._minarray[number] = minimum
            self._maxarray[number] = maximum
            self._steparray[number] = stepsize
            self._clickarray[number] = clicks
            temp_value = self._spinboxes[number].value()
            self._sliders[number].setMaximum(clicks)
            self._spinboxes[number].setMinimum(minimum)
            self._spinboxes[number].setMaximum(maximum)
            self._spinboxes[number].setSingleStep(stepsize)
            self._spinboxes[number].setDecimals(abs(int(np.floor(np.log10(stepsize)))))
            temp_value = min(maximum, temp_value)
            temp_value = max(minimum, temp_value)
            click_value = int(round((temp_value - minimum) / stepsize))
            self._sliders[number].setValue(click_value)
            self._spinboxes[number].setValue(temp_value)

    def set_values(self, new_values: list[float]):
        """Set both spinboxes and sliders to the new incoming values.

        Values will be replaced with maximum/minimum values allowed by
        the slider if the input values are outside of the current limits.

        Parameters
        ----------
        new_values : list[float]
            One new value per slider

        """
        nv = np.array(new_values)
        nv = np.maximum(nv, self._minarray)
        nv = np.minimum(nv, self._maxarray)
        clicks = np.round((nv - self._minarray) / self._steparray).astype(int)
        for n in range(len(nv)):
            self._spinboxes[n].setValue(nv[n])
            self._sliders[n].setValue(clicks[n])

    @Slot()
    def slider_to_box(self):
        """Update spin boxes if slider is moving."""
        vals = np.zeros_like(self._valarray)
        clicks = np.zeros_like(self._clickarray)
        for ns, slider in enumerate(self._sliders):
            clicks[ns] = slider.value()
        vals = self._minarray + clicks * self._steparray
        for ns, box in enumerate(self._spinboxes):
            box.setValue(vals[ns])

    @Slot()
    def box_to_slider(self):
        """Update sliders if spin boxes have changed."""
        self.blockSignals(True)
        vals = np.zeros_like(self._valarray)
        clicks = np.zeros_like(self._clickarray)
        for ns, box in enumerate(self._spinboxes):
            vals[ns] = box.value()
        clicks = np.round((vals - self._minarray) / self._steparray).astype(int)
        for ns, slider in enumerate(self._sliders):
            slider.setValue(clicks[ns])
        self.slider_to_box()
        self.blockSignals(False)

    @Slot()
    def collect_values(self):
        """Get and emit current values from all sliders/spinboxes."""
        result = []
        for box in self._spinboxes:
            result.append(box.value())
        self._current_values = result
        self.new_values.emit(result)


class PlotWidget(QWidget):
    """Plotting area with controls."""

    change_slider_labels = Signal(object)
    change_slider_limits = Signal(object)
    reset_slider_values = Signal(bool)
    change_slider_coupling = Signal(bool)

    def __init__(self, *args, **kwargs) -> None:
        """Create an empty plot with the default plotter."""
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._sliderpack = None
        self._normaliser = None
        self._plotting_context = None
        self._slider_max = 100
        self.unique_id = -1
        self.make_canvas()
        self.set_plotter("Single")

    def set_context(self, new_context: PlottingContext):
        """Assign a data model to the plot widget."""
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure
        self.unique_id = id(self)
        self._plotting_context.plot_widget_id = self.unique_id

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        """Change the class handling the plot operation.

        Parameters
        ----------
        plotter_option : str
            Plotter name

        """
        try:
            self._plotter = Plotter.create(plotter_option)
        except Exception:
            self._plotter = Plotter()
        self.change_slider_labels.emit(self._plotter.slider_labels())
        self.change_slider_limits.emit(self._plotter.slider_limits())
        self.change_slider_coupling.emit(self._plotter.sliders_coupled())
        self.reset_slider_values.emit(self._plotter._value_reset_needed)
        self._plotter._slider_reference = self._sliderpack
        self._sliderpack.setEnabled(False)
        self.plot_data()

    @Slot(object)
    def slider_change(self, new_values: object):
        """Pass the new slider values to the plotter."""
        self._plotter.handle_slider(new_values)

    @Slot(dict)
    def normaliser_change(self, new_values: dict):
        """Pass the new normalisation parameters to the plotter."""
        self._plotter.change_normalisation(new_values)
        self.mark_normalisation()

    @Slot(bool)
    def set_slider_values(self, reset_needed: bool):
        """Adjust the slider values if plotter type has changed.

        Parameters
        ----------
        reset_needed : bool
            True if the new plotter uses the sliders differently.
            If True, will set the sliders to the default values for
            this plotter type.

        """
        if reset_needed and self._sliderpack is not None:
            values = self._plotter._initial_values
            self._sliderpack.set_values(values)

    def available_plotters(self) -> list[str]:
        """List all the plotters supported by this widget."""
        return [str(x) for x in Plotter.indirect_subclasses() if str(x) != "Text"]

    def plot_blank(self):
        """Show a blank plot to indicate that plotting failed."""
        LOG.debug("PlotWidget is about to call self._plotter.plot_blank()")
        if self._plotter is None:
            self._plotter = Plotter()
        self._plotter.plot_blank()

    @Slot()
    def use_legend(self, bool_flag: bool | None = None):
        if bool_flag is None:
            bool_flag = self._legend_box.isChecked()
        if self._plotting_context:
            self._plotting_context.use_legend = bool_flag
            self._plotting_context.ask_for_update()

    @Slot()
    def use_grid(self, bool_flag: bool | None = None):
        if bool_flag is None:
            bool_flag = self._grid_box.isChecked()
        if self._plotting_context:
            self._plotting_context.use_grid = bool_flag
            self._plotting_context.ask_for_update()

    def plot_data(self, update_only=False):
        """Use the internal plotter instance to create a plot.

        Parameters
        ----------
        update_only : bool, optional
            If true, will re-use existing plot elements, by default False

        """
        if self._plotter is None:
            LOG.info("No plotter present in PlotWidget.")
            return
        if self._plotting_context is None:
            return
        self._plotter.plot(
            self._plotting_context,
            self._figure,
            update_only=update_only,
            toolbar=self._toolbar,
        )
        self._normaliser.update_spinbox_limits(self._plotter.curve_length_limit)
        self._normaliser.collect_values()
        self._sliderpack.collect_values()
        self.mark_normalisation()

    def mark_normalisation(self):
        """Indicate in the GUI if normalisation failed for some curves."""
        if self._plotter._normalisation_errors:
            self._normaliser.mark_error("\n".join(self._plotter._normalisation_errors))
        else:
            self._normaliser.clear_error()

    def make_canvas(self):
        """Create a matplotlib figure for plotting.

        Parameters
        ----------
        width : float, optional
            Figure width in inches, by default 12.0
        height : float, optional
            Figure height in inches, by default 9.0
        dpi : int, optional
            Figure resolution in dots per inch, by default 100

        Returns
        -------
        QWidget
            a widget containing both the figure and a toolbar below

        """
        canvas = self
        layout = QVBoxLayout(canvas)
        figure = mpl.figure()
        figAgg = FigureCanvasQTAgg(figure)
        figAgg.setParent(canvas)
        figAgg.updateGeometry()
        toolbar = NavigationToolbar2QTAgg(figAgg, canvas)
        toolbar.update()
        layout.addWidget(figAgg)
        normaliser = NormalisationWidget(self)
        slider = SliderPack(self)
        self.change_slider_labels.connect(slider.new_slider_labels)
        self.change_slider_limits.connect(slider.new_limits)
        self.change_slider_coupling.connect(slider.new_coupling)
        self.reset_slider_values.connect(self.set_slider_values)
        slider.new_values.connect(self.slider_change)
        normaliser.new_values.connect(self.normaliser_change)
        self._sliderpack = slider
        self._normaliser = normaliser
        # Matplotlib control widgets, next to the toolbar.
        temp_hlayout = QHBoxLayout()
        temp_hlayout.addWidget(toolbar)
        legend_box = QCheckBox(text="Legend")
        grid_box = QCheckBox(text="Grid")
        legend_box.clicked.connect(self.use_legend)
        grid_box.clicked.connect(self.use_grid)
        temp_hlayout.addWidget(legend_box)
        temp_hlayout.addWidget(grid_box)
        # The following widgets are placed below the plot.
        layout.addLayout(temp_hlayout)
        layout.addWidget(slider)
        layout.addWidget(normaliser)
        self._legend_box = legend_box
        self._grid_box = grid_box
        self._legend_box.setChecked(True)
        self._grid_box.setChecked(True)
        self._figure = figure
        self._toolbar = toolbar
        plot_selector = QComboBox(self)
        layout.addWidget(plot_selector)
        plot_selector.addItems(self.available_plotters())
        plot_selector.setCurrentText("Single")
        plot_selector.currentTextChanged.connect(self.set_plotter)
        self.set_plotter(plot_selector.currentText())
