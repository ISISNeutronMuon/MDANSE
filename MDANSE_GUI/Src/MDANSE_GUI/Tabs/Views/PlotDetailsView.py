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

from qtpy.QtWidgets import QTreeView
from qtpy.QtCore import Signal

from MDANSE_GUI.Tabs.Views.Delegates import ColourPicker, MplStyleCombo
from MDANSE_GUI.Tabs.Models.PlottingContext import get_mpl_lines, get_mpl_markers


class PlotDetailsView(QTreeView):
    details_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegates = {
            "colour": ColourPicker(),
            "line": MplStyleCombo(mpl_items=get_mpl_lines()),
            "marker": MplStyleCombo(mpl_items=get_mpl_markers()),
        }
        self.setItemDelegateForColumn(5, self._delegates["colour"])
        self.setItemDelegateForColumn(6, self._delegates["line"])
        self.setItemDelegateForColumn(7, self._delegates["marker"])

    def connect_to_visualiser(self, visualiser) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.
        """
        self.details_changed.connect(visualiser.update_plot_details)
