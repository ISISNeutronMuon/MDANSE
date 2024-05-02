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

import matplotlib.pyplot as mpl

from qtpy.QtWidgets import QWidget, QVBoxLayout
from qtpy.QtCore import Slot, Signal


unit_lookup = {
    "rad/ps": "energy",
    "nm": "distance",
    "ps": "time",
}


class SingleDataset:

    def __init__(self, name: str, source: "h5py.File"):
        self._name = name
        self._filename = source.filename
        self._data = source[name][:]
        self._data_unit = source[name].attrs["units"]
        self._axes_tag = source[name].attrs["axis"]
        self._axes = {}
        self._axes_units = {}
        for axis_name in self._axes_tag.split("|"):
            aname = axis_name.strip()
            self._axes[aname] = source[aname][:]
            self._axes_units = source[name].attrs["units"]


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
        dataset = self._datasets[0]
        n_dimensions = len(dataset._data.shape)
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

    def plot_datasets(self, figure: Figure = None):
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
            axes = figure.add_axes("111")


class DataPlotter(QWidget):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

    @Slot(object)
    def plot_data(self, data_set):
        print(f"Received {data_set}")

    @Slot()
    def clear(self):
        print(f"Cleared the plot")
