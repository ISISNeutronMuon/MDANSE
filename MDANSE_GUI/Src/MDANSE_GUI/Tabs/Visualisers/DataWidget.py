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
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext

import numpy as np
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextBrowser,
    QGridLayout,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QCheckBox,
)
from qtpy.QtCore import Slot, Signal, Qt

from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter


class DataWidget(QWidget):

    change_slider_labels = Signal(object)
    change_slider_limits = Signal(object)
    reset_slider_values = Signal(bool)
    change_slider_coupling = Signal(bool)

    def __init__(self, *args, colours=None, settings=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._sliderpack = None
        self._plotting_context = None
        self._colours = colours
        self._settings = settings
        self._slider_max = 100
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.make_toolbar()
        self.make_canvas()
        self.set_plotter("Text")
        self.update_plotter_params()

    def make_toolbar(self, line_length=6):
        layout = QGridLayout()
        self.layout().addLayout(layout)
        self._preview_widget = QCheckBox(self)
        self._preview_widget.setChecked(True)
        self._preview_widget.checkStateChanged.connect(self.update_plotter_params)
        self._separator_widget = QLineEdit(" ", self)
        self._separator_widget.textChanged.connect(self.update_plotter_params)
        self._comment_widget = QLineEdit("#", self)
        self._comment_widget.textChanged.connect(self.update_plotter_params)
        self._precision_widget = QSpinBox(self)
        self._precision_widget.setValue(5)
        self._precision_widget.valueChanged.connect(self.update_plotter_params)
        self._lines_widget = QSpinBox(self)
        self._lines_widget.setValue(10)
        self._lines_widget.valueChanged.connect(self.update_plotter_params)
        self._columns_widget = QSpinBox(self)
        self._columns_widget.setValue(10)
        self._columns_widget.valueChanged.connect(self.update_plotter_params)
        # populate the layout
        column = 0
        row = 0
        for label_text, widget in [
            ("Preview only (truncate)", self._preview_widget),
            ("Preview lines:", self._lines_widget),
            ("Preview columns:", self._columns_widget),
            ("Rounding precision", self._precision_widget),
            ("Separator character", self._separator_widget),
            ("Comment character", self._comment_widget),
        ]:
            layout.addWidget(QLabel(label_text, self), row, column)
            column += 1
            layout.addWidget(widget, row, column)
            column += 1
            if column >= line_length:
                row += 1
                column = 0

    @Slot(object)
    def slider_change(self, new_values: object):
        """Not used for text output."""

    @Slot(bool)
    def set_slider_values(self, reset_needed: bool):
        """Not used for text output."""

    def set_context(self, new_context: "PlottingContext"):
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        try:
            self._plotter = Plotter.create(plotter_option)
        except Exception as e:
            LOG.error(f"DataWidget failed to create Text plotter: {e}")
        else:
            LOG.debug(f"DataWidget created plotter {plotter_option}: {self._plotter}")
            self._plotter._settings = self._settings
            self.plot_data()

    @Slot()
    def update_plotter_params(self):
        if self._plotter is None:
            return
        is_preview = self._preview_widget.isChecked()
        rounding_precision = self._precision_widget.value()
        comment_char = self._comment_widget.text()
        separator_char = self._separator_widget.text()
        preview_lines = self._lines_widget.value()
        preview_columns = self._columns_widget.value()
        self._plotter.adjust_formatter(
            preview=is_preview,
            preview_lines=preview_lines,
            preview_columns=preview_columns,
            rounding=rounding_precision,
            separator=separator_char,
            comment=comment_char,
        )

    @Slot(object)
    def slider_change(self, new_values: object):
        self._plotter.handle_slider(new_values)

    @Slot(bool)
    def set_slider_values(self, reset_needed: bool):
        if reset_needed and self._sliderpack is not None:
            values = self._plotter._initial_values
            self._sliderpack.set_values(values)

    def available_plotters(self) -> List[str]:
        return ["Text"]

    def plot_data(self, update_only=False):
        if self._plotter is None:
            LOG.info("No plotter present in DataWidget.")
            return
        if self._plotting_context is None:
            LOG.info("No plotting context present in DataWidget.")
            return
        try:
            LOG.debug(
                f"DataWidget will plot {self._plotting_context} in {self._figure}."
            )
            self._plotter.plot(
                self._plotting_context,
                self._figure,
                colours=None,
                update_only=None,
                toolbar=None,
            )
        except Exception as e:
            LOG.error(f"DataWidget error: {e}")

    def make_canvas(self):
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
            a widget containing just a QTextBrowser
        """
        layout = self.layout()
        self._figure = QTextBrowser(self)
        layout.addWidget(self._figure)
