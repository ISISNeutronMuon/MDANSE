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

from itertools import islice
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as mpl
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from more_itertools import ilen
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.PlotUtils import MDANSEMatPlotLibNavBar
from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter, ValidPlotters
from MDANSE_GUI.Utils import block_signals
from MDANSE_GUI.Widgets.NormalisationWidget import NormalisationWidget
from MDANSE_GUI.Widgets.RestrictedSlider import RestrictedSlider

if TYPE_CHECKING:
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class SliderPack(QWidget):
    """Widget combining several RestrictedSlider instances.

    Parameters
    ----------
    n_sliders : int
        Number of sliders to add.
    """

    new_values = Signal(object)

    def __init__(self, *args, n_sliders: int = 2, **kwargs) -> None:
        """Create the widget with the specified number of sliders."""
        super().__init__(*args, **kwargs)
        layout = QGridLayout(self)
        self.setLayout(layout)

        self._labels = [QLabel(self) for _ in range(n_sliders)]
        self._sliders = [
            RestrictedSlider(Qt.Orientation.Horizontal, self) for _ in range(n_sliders)
        ]
        self._spinboxes = [QDoubleSpinBox(self) for _ in range(n_sliders)]

        for n, (label, slider, box) in enumerate(
            zip(self._labels, self._sliders, self._spinboxes, strict=True)
        ):
            layout.addWidget(label, n, 0)
            layout.addWidget(slider, n, 1, 1, 2)
            layout.addWidget(box, n, 3)

            box.setSingleStep(0.01)
            box.valueChanged.connect(self.box_to_slider)
            box.valueChanged.connect(self.collect_values)

            slider.valueChanged.connect(self.slider_to_box)

    @Slot(bool)
    def new_coupling(self, new_val: bool):
        """Couples the first two sliders together if new_val is true.

        Parameters
        ----------
        new_val : bool
            True for coupled sliders, false otherwise

        """
        for slider in islice(self._sliders, 2):
            slider._coupled = new_val

    @Slot(object)
    def new_slider_labels(self, input_labels: list[str]):
        """Change the text labels of the sliders to new values."""
        for label, element in zip(self._labels, input_labels, strict=True):
            label.setText(element)

    @Slot(object)
    def new_limits(self, input_limits: list[tuple[float, float, float]]):
        """Change the limits and step number of the sliders.

        Since QSlider works with integer numbers, the float
        values of limits are used in the spin boxes, while
        the sliders work with integer 'clicks' in the background.

        Parameters
        ----------
        input_limits : list[tuple[float, float, float]]
            For each slider, [minimum, maximum, step_size] values

        """
        for (minimum, maximum, stepsize), box, slider in zip(
            input_limits, self._spinboxes, self._sliders, strict=True
        ):
            clicks = round((maximum - minimum) / stepsize)

            slider.setRange(0, clicks)

            temp_value = np.clip(box.value(), minimum, maximum)
            box.setRange(minimum, maximum)
            box.setSingleStep(stepsize)
            box.setDecimals(abs(int(np.floor(np.log10(stepsize)))))
            box.setValue(temp_value)
        self.box_to_slider()

    def set_values(self, new_values: list[float]):
        """Set both spinboxes and sliders to the new incoming values.

        Values will be replaced with maximum/minimum values allowed by
        the slider if the input values are outside of the current limits.

        Parameters
        ----------
        new_values : list[float]
            One new value per slider

        """
        for box, val in zip(self._spinboxes, new_values, strict=True):
            box.setValue(np.clip(val, box.minimum(), box.maximum()))
        self.box_to_slider()

    @property
    def slider_values(self) -> list[float]:
        """Values returned from sliders (as ints [clicks])."""
        return [slider.value() for slider in self._sliders]

    @property
    def box_values(self) -> list[float]:
        """Values returned from boxes (as floats)."""
        return [box.value() for box in self._spinboxes]

    @Slot()
    def slider_to_box(self):
        """Update spin boxes if slider is moving."""
        with block_signals(self, *self._spinboxes):
            for box, slider in zip(
                self._spinboxes,
                self._sliders,
                strict=True,
            ):
                box.setValue(box.minimum() + (slider.value() * box.singleStep()))
        self.box_to_slider()

    @Slot()
    def box_to_slider(self):
        """Update sliders if spin boxes have changed."""
        with block_signals(self, *self._sliders):
            for slider, box in zip(
                self._sliders,
                self._spinboxes,
                strict=True,
            ):
                slider.setValue(round((box.value() - box.minimum()) / box.singleStep()))
        self.collect_values()

    @Slot()
    def collect_values(self):
        """Get and emit current values from all sliders/spinboxes."""
        self._current_values = self.box_values
        self.new_values.emit(self.box_values)


class PlotWidget(QWidget):
    """Plotting area with controls."""

    change_slider_labels = Signal(object)
    change_slider_limits = Signal(object)
    reset_slider_values = Signal(bool)
    change_slider_coupling = Signal(bool)

    def __init__(
        self,
        *args,
        plotter_type: ValidPlotters = "Single",
        **kwargs,
    ) -> None:
        """Create an empty plot with the default plotter."""
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._sliderpack = None
        self._normaliser = None
        self._plotting_context = None
        self._slider_max = 100
        self.unique_id = -1
        self.make_canvas()
        self.set_plotter(plotter_type)

        if plotter_type != "Single":
            self.plot_selector.setCurrentText(plotter_type)

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
        self._plotter._figure = self._figure
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
        return [str(x) for x in Plotter.raw_names() if str(x) != "Text"]

    def plot_blank(
        self,
        *,
        draw_cross: bool = True,
        override_title: str | None = None,
        override_label: str | None = None,
    ):
        """Show a blank plot to indicate that plotting failed."""
        LOG.debug("PlotWidget is about to call self._plotter.plot_blank()")
        if self._plotter is None:
            self._plotter = Plotter()
        self._plotter.plot_blank(
            draw_cross=draw_cross,
            override_title=override_title,
            override_label=override_label,
        )

    @Slot()
    def use_legend(self, override: bool | None = None):
        if override is None:
            override = self._legend_box.isChecked()
        if self._plotting_context:
            self._plotting_context.use_legend = override
        if self._plotter:
            self._plotter.toggle_legend(override)

    @Slot()
    def use_grid(self, override: bool | None = None):
        if override is None:
            override = self._grid_box.isChecked()
        if self._plotting_context:
            self._plotting_context.use_grid = override
        if self._plotter:
            self._plotter.toggle_grid(override)

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
        self._figure.set_layout_engine("tight")
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

        self._figure = mpl.figure(layout="constrained")
        figAgg = FigureCanvasQTAgg(self._figure)
        figAgg.setParent(canvas)
        figAgg.updateGeometry()
        layout.addWidget(figAgg, stretch=1)

        # Matplotlib control widgets, next to the toolbar.

        self._toolbar = MDANSEMatPlotLibNavBar(figAgg, canvas)
        self._toolbar.update()

        self._legend_box = QCheckBox(text="Legend")
        self._legend_box.clicked.connect(self.use_legend)
        self._legend_box.setChecked(True)

        self._grid_box = QCheckBox(text="Grid")
        self._grid_box.clicked.connect(self.use_grid)
        self._grid_box.setChecked(True)

        self._save_button = QPushButton("Save Data", self)
        self._save_button.pressed.connect(self._save_data)
        self._save_button.setToolTip("Save data in plot to a csv file.")
        self._file_dialog = QFileDialog.getSaveFileName

        temp_hlayout = QHBoxLayout()
        temp_hlayout.addWidget(self._toolbar)
        temp_hlayout.addWidget(self._legend_box)
        temp_hlayout.addWidget(self._grid_box)
        temp_hlayout.addWidget(self._save_button)
        layout.addLayout(temp_hlayout)

        # The following widgets are placed below the plot.

        self._sliderpack = SliderPack(self)
        self.change_slider_labels.connect(self._sliderpack.new_slider_labels)
        self.change_slider_limits.connect(self._sliderpack.new_limits)
        self.change_slider_coupling.connect(self._sliderpack.new_coupling)
        self.reset_slider_values.connect(self.set_slider_values)
        self._sliderpack.new_values.connect(self.slider_change)
        layout.addWidget(self._sliderpack)

        self._normaliser = NormalisationWidget(self)
        self._normaliser.new_values.connect(self.normaliser_change)
        layout.addWidget(self._normaliser)

        self.plot_selector = QComboBox(self)
        self.plot_selector.addItems(self.available_plotters())
        self.plot_selector.setCurrentText("Single")
        self.plot_selector.currentTextChanged.connect(self.set_plotter)
        self.set_plotter(self.plot_selector.currentText())
        layout.addWidget(self.plot_selector)
        self.hide_plotters()

    def hide_plotters(self):
        model = self.plot_selector.model()
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            item = model.itemFromIndex(index)
            item_text = model.data(index)
            if item_text in ("Text", "Vectors", "Vectors3D"):
                item.setSelectable(False)

    def _save_data(self) -> None:
        plotter = self._plotter
        if not plotter._figure or not any(
            ilen(plotter._get_datasets(ax)) for ax in plotter._figure.axes
        ):
            QMessageBox.warning(self, "No data", "No data in plot.")
            return

        save_loc, _ = self._file_dialog(
            parent=self,
            caption="Save file",
            directory=str(Path.cwd()),
            filter="Data files (*.dat);;All files (*)",
        )

        self._plotter.save_data(save_loc)
