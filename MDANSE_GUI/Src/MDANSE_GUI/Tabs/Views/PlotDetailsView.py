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

import matplotlib.pyplot as mpl
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QTreeView

from MDANSE_GUI.Tabs.Models.PlottingContext import (
    get_mpl_lines,
    get_mpl_markers,
    plotting_column_index,
)
from MDANSE_GUI.Tabs.Views.Delegates import ColourPicker, MainAxisCombo, MplStyleCombo

if TYPE_CHECKING:
    from qtpy.QtWidgets import QItemDelegate, QTableView


def set_plot_table_delegates(
    view: QTreeView | QTableView, delegates: dict[str, QItemDelegate]
):
    """Attach delegates to specific columns of a Qt view.

    This is used to simplify the input and validation of dataset attributes
    used in the MDANSE_GUI plotter. By applying the same delegates to views
    in different tabs, we ensure that the same inputs will be considered valid.

    Parameters
    ----------
    view : QTreeView | QTableView
        View containing plottable datasets.
    delegates : dict[str, QItemDelegate]
        A dictionary of QItemDelegate subclasses.
    """
    view.setItemDelegateForColumn(
        plotting_column_index["Colour 1"], delegates["colour 1"]
    )
    view.setItemDelegateForColumn(
        plotting_column_index["Colour 2"], delegates["colour 2"]
    )
    view.setItemDelegateForColumn(
        plotting_column_index["Colour map"], delegates["colour map"]
    )
    view.setItemDelegateForColumn(
        plotting_column_index["Line style"], delegates["line"]
    )
    view.setItemDelegateForColumn(plotting_column_index["Marker"], delegates["marker"])
    view.setItemDelegateForColumn(plotting_column_index["Main axis"], delegates["axis"])


class PlotDetailsView(QTreeView):
    details_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegates = {
            "colour 1": ColourPicker(),
            "colour 2": ColourPicker(),
            "axis": MainAxisCombo(),
            "colour map": MplStyleCombo(mpl_items=mpl.colormaps()),
            "line": MplStyleCombo(mpl_items=get_mpl_lines()),
            "marker": MplStyleCombo(mpl_items=get_mpl_markers()),
        }
        set_plot_table_delegates(self, self._delegates)

    def connect_to_visualiser(self, visualiser) -> None:
        """Dummy method. The PlottingContext model is connected to the plotter directly."""
