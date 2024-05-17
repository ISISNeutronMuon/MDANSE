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

from PyQt6.QtCore import Qt
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from qtpy.QtWidgets import QWidget, QVBoxLayout, QComboBox
from qtpy.QtCore import Slot, Signal, QObject

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter


class PlotWidget(QWidget):

    def __init__(self, *args, colours=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._plotter = None
        self._plotting_context = None
        self._colours = colours
        self.make_canvas()

    def set_context(self, new_context: "PlottingContext"):
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        try:
            self._plotter = Plotter.create(plotter_option)
        except:
            self._plotter = Plotter()
        self.plot_data()

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
        layout.addWidget(toolbar)
        self._figure = figure
        plot_selector = QComboBox(self)
        layout.addWidget(plot_selector)
        plot_selector.addItems(self.available_plotters())
        plot_selector.setCurrentText("Single")
        plot_selector.currentTextChanged.connect(self.set_plotter)
        self.set_plotter(plot_selector.currentText())
