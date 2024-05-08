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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import h5py
    from matplotlib.figure import Figure

from PyQt6.QtCore import Qt
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from qtpy.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from qtpy.QtCore import Slot, Signal, QObject


unit_lookup = {"rad/ps": "energy", "nm": "distance", "ps": "time", "N/A": "arbitrary"}


class SingleDataset:

    def __init__(self, name: str, source: "h5py.File"):
        self._name = name
        self._filename = source.filename
        self._valid = True
        try:
            self._data = source[name][:]
        except KeyError:
            print(f"{name} is not a data set in the file")
            self._valid = False
            return
        except TypeError:
            self._valid = False
            print(f"{name} is not plottable")
            return
        self._data_unit = source[name].attrs["units"]
        self._axes_tag = source[name].attrs["axis"]
        self._axes = {}
        self._axes_units = {}
        for axis_name in self._axes_tag.split("|"):
            aname = axis_name.strip()
            if aname == "index":
                self._axes[aname] = range(len(self._data))
                self._axes_units[aname] = "N/A"
            else:
                self._axes[aname] = source[aname][:]
                self._axes_units[aname] = source[aname].attrs["units"]


class PlottingContext:

    def __init__(self, unit_preference=None):
        self._datasets = {}
        self._current_axis = [None, None, None]
        self._figure = None
        if unit_preference is None:
            self._unit_preference = {}
        else:
            self._unit_preference = unit_preference

    def add_dataset(self, new_dataset: SingleDataset):
        newkey = f"{new_dataset._filename}:{new_dataset._name}"
        self._datasets[newkey] = new_dataset

    def set_axes(self):
        if len(self._datasets) == 0:
            return
        for dataset in self._datasets.values():
            n_dimensions = len(dataset._data.shape)
            # some extra code needed here
        axis_count = 0
        for name, unit in dataset._axes_units.items():
            if self._current_axis[axis_count] is None:
                quantity = unit_lookup[unit]
                if quantity in self._unit_preference:
                    new_unit = self._unit_preference[quantity]
                else:
                    new_unit = unit
                self._current_axis[axis_count] = new_unit
            axis_count += 1
        if not axis_count == n_dimensions:
            print(
                f"PlottingContext found {axis_count} axes for {n_dimensions} dimensions. Stopped."
            )
            return
        self._ndim = n_dimensions
        return "Configured!"

    def plot_datasets(self, figure: "Figure" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            print(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        if self.set_axes() is None:
            print("Axis check failed.")
            return
        for dataset in self._datasets:
            axes = target.add_axes("111")
            xtags = list(dataset._axes.keys())
            axes.plot(dataset._axes[xtags[0]], dataset._data)


class PlotWidget(QWidget):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.make_canvas()
        self._plotting_context = None

    def set_context(self, new_context: PlottingContext):
        self._plotting_context = new_context
        self._plotting_context._figure = self._figure

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


class DataPlotter(QTabWidget):
    """This is the top-layer widget which will host any number of
    PlotWidgets.
    """

    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self._context = {}
        self._plotter = {}
        self._current_id = -1
        self.setLayout(layout)
        self._current_id = self.new_plot("preview")

    @Slot(str)
    def new_plot(self, tab_name: str) -> int:
        try:
            preferred_units = self._session._units
        except:
            preferred_units = None
        plotting_context = PlottingContext(unit_preference=preferred_units)
        plotter = PlotWidget(self)
        plotter.set_context(plotting_context)
        tab_id = self.addTab(plotter, tab_name)
        self._context[tab_id] = plotting_context
        self._plotter[tab_id] = plotter
        return tab_id

    @Slot(object)
    def plot_data(self, data_set):
        print(f"Received {data_set}")
        dataset = SingleDataset(data_set[0], data_set[1])
        context = self._context[self._current_id]
        if dataset._valid:
            context.add_dataset(dataset)
        context.set_axes()
        context.plot_datasets()

    @Slot()
    def clear(self):
        print(f"Cleared the plot")
