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
from qtpy.QtCore import Slot, Signal, QObject, QModelIndex
from qtpy.QtGui import QStandardItemModel, QStandardItem


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


class PlottingContext(QStandardItemModel):

    def __init__(self, *args, unit_preference=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._datasets = {}
        self._current_axis = [None, None, None]
        self._figure = None
        if unit_preference is None:
            self._unit_preference = {}
        else:
            self._unit_preference = unit_preference
        self.setHorizontalHeaderLabels(
            ["Dataset", "Trajectory", "Size", "Unit", "Use it?"]
        )

    @Slot(object)
    def accept_external_data(self, other: "PlottingContext"):
        """Crucial slot for transferring data
        between tabs. DataPlotter will send the datasets
        into this slot."""
        for dataset in other._datasets.values():
            self.add_dataset(dataset)
        self.set_axes()

    def add_dataset(self, new_dataset: SingleDataset):
        if not new_dataset._valid:
            return
        newkey = f"{new_dataset._filename}:{new_dataset._name}"
        if newkey in self._datasets:
            return
        self._datasets[newkey] = new_dataset
        items = [
            QStandardItem(str(x))
            for x in [
                new_dataset._name,
                new_dataset._filename,
                new_dataset._data.shape,
                new_dataset._data_unit,
                "",
            ]
        ]
        for item in items:
            item.setData(newkey, role=Qt.ItemDataRole.UserRole)
            item.setEditable(False)
        temp = items[4]
        temp.setCheckable(True)
        temp.setCheckState(Qt.CheckState.Checked)
        self.appendRow(items)

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

    @Slot()
    def clear(self) -> None:
        result = super().clear()
        self._datasets = {}
        return result

    @Slot(QModelIndex)
    def delete_dataset(self, index: QModelIndex):
        dkey = index.data(role=Qt.ItemDataRole.UserRole)
        self.removeRow(index.row())
        self._datasets.pop(dkey, None)
