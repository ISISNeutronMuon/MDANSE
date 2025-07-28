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

from qtpy.QtCore import Signal
from qtpy.QtWidgets import QTreeView

from MDANSE_GUI.Tabs.Models.PlottingContext import (
    get_mpl_lines,
    get_mpl_markers,
    plotting_column_index,
)
from MDANSE_GUI.Tabs.Views.Delegates import ColourPicker, MainAxisCombo, MplStyleCombo


class PlotDetailsView(QTreeView):
    details_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegates = {
            "colour": ColourPicker(),
            "axis": MainAxisCombo(),
            "line": MplStyleCombo(mpl_items=get_mpl_lines()),
            "marker": MplStyleCombo(mpl_items=get_mpl_markers()),
        }
        self.setItemDelegateForColumn(
            plotting_column_index["Colour"], self._delegates["colour"]
        )
        self.setItemDelegateForColumn(
            plotting_column_index["Line style"], self._delegates["line"]
        )
        self.setItemDelegateForColumn(
            plotting_column_index["Marker"], self._delegates["marker"]
        )
        self.setItemDelegateForColumn(
            plotting_column_index["Main axis"], self._delegates["axis"]
        )

    def connect_to_visualiser(self, visualiser) -> None:
        """Dummy method. The PlottingContext model is connected to the plotter directly."""
