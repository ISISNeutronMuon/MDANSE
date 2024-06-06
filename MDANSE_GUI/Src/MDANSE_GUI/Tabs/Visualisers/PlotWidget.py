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

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext

import numpy as np
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QSlider,
    QLabel,
    QGridLayout,
    QRadioButton,
    QButtonGroup,
    QDoubleSpinBox,
)
from qtpy.QtCore import Slot, Signal, QObject, Qt

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter


class SliderPack(QWidget):

    new_values = Signal(object)

    def __init__(self, *args, n_sliders=2, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        layout = QGridLayout(self)
        self.setLayout(layout)
        self._labels = []
        self._sliders = []
        self._spinboxes = []
        self._minarray = np.zeros(n_sliders)
        self._maxarray = np.ones(n_sliders)
        self._valarray = np.ones(n_sliders) * 0.5
        self._steparray = np.ones(n_sliders) * 0.01
        self._clickarray = np.array(n_sliders * [101], dtype=int)
        current_row = 0
        for n in range(n_sliders):
            label = QLabel(self)
            slider = QSlider(self)
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

    @Slot(object)
    def new_slider_labels(self, input):
        for number, element in enumerate(input):
            self._labels[number].setText(element)

    @Slot(object)
    def new_limits(self, input):
        for number, element in enumerate(input):
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
            temp_value = min(maximum, temp_value)
            temp_value = max(minimum, temp_value)
            click_value = int(round((temp_value - minimum) / stepsize))
            self._sliders[number].setValue(click_value)
            self._spinboxes[number].setValue(temp_value)

    def set_values(self, new_values: List[float]):
        nv = np.array(new_values)
        nv = np.maximum(nv, self._minarray)
        nv = np.minimum(nv, self._maxarray)
        clicks = np.round((nv - self._minarray) / self._steparray).astype(int)
        for n in range(len(nv)):
            self._spinboxes[n].setValue(nv[n])
            self._sliders[n].setValue(clicks[n])

    @Slot()
    def slider_to_box(self):
        vals = np.zeros_like(self._valarray)
        clicks = np.zeros_like(self._clickarray)
        for ns, slider in enumerate(self._sliders):
            clicks[ns] = slider.value()
        vals = self._minarray + clicks * self._steparray
        for ns, box in enumerate(self._spinboxes):
            box.setValue(vals[ns])

    @Slot()
    def box_to_slider(self):
        self.blockSignals(True)
        vals = np.zeros_like(self._valarray)
        clicks = np.zeros_like(self._clickarray)
        for ns, box in enumerate(self._spinboxes):
            vals[ns] = box.value()
        clicks = np.round((vals - self._minarray) / self._steparray).astype(int)
        for ns, slider in enumerate(self._sliders):
            slider.setValue(clicks[ns])
        self.blockSignals(False)

    @Slot()
    def collect_values(self):
        result = []
        for box in self._spinboxes:
            result.append(box.value())
        self.new_values.emit(result)


class PlotWidget(QWidget):

    change_slider_labels = Signal(object)
    change_slider_limits = Signal(object)
    reset_slider_values = Signal(bool)

    def __init__(self, *args, colours=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._sliderpack = None
        self._plotting_context = None
        self._colours = colours
        self._slider_max = 100
        self.make_canvas()
        self.set_plotter("Single")

    def set_context(self, new_context: "PlottingContext"):
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        try:
            self._plotter = Plotter.create(plotter_option)
        except:
            self._plotter = Plotter()
        self.change_slider_labels.emit(self._plotter.slider_labels())
        self.change_slider_limits.emit(self._plotter.slider_limits())
        self.reset_slider_values.emit(self._plotter._value_reset_needed)
        self.plot_data()

    @Slot(object)
    def slider_change(self, new_values: object):
        self._plotter.handle_slider(new_values)

    @Slot(bool)
    def set_slider_values(self, reset_needed: bool):
        if reset_needed and self._sliderpack is not None:
            values = self._plotter._initial_values
            self._sliderpack.set_values(values)

    def available_plotters(self) -> List[str]:
        return [str(x) for x in Plotter.indirect_subclasses()]

    def plot_data(self):
        if self._plotter is None:
            print("No plotter present in PlotWidget.")
            return
        if self._plotting_context is None:
            return
        self._plotter.plot(self._plotting_context, self._figure, colours=self._colours)

    def make_canvas(self, width=12.0, height=9.0, dpi=100):
        """Creates a matplotlib figure for plotting

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
        figure = mpl.figure(figsize=[width, height], dpi=dpi, frameon=True)
        figAgg = FigureCanvasQTAgg(figure)
        figAgg.setParent(canvas)
        figAgg.updateGeometry()
        toolbar = NavigationToolbar2QTAgg(figAgg, canvas)
        toolbar.update()
        layout.addWidget(figAgg)
        slider = SliderPack(self)
        self.change_slider_labels.connect(slider.new_slider_labels)
        self.change_slider_limits.connect(slider.new_limits)
        self.reset_slider_values.connect(self.set_slider_values)
        slider.new_values.connect(self.slider_change)
        self._sliderpack = slider
        layout.addWidget(slider)
        layout.addWidget(toolbar)
        self._figure = figure
        plot_selector = QComboBox(self)
        layout.addWidget(plot_selector)
        plot_selector.addItems(self.available_plotters())
        plot_selector.setCurrentText("Single")
        plot_selector.currentTextChanged.connect(self.set_plotter)
        self.set_plotter(plot_selector.currentText())
