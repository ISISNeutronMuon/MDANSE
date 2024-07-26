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
from qtpy.QtWidgets import QLineEdit, QLabel
from qtpy.QtGui import QDoubleValidator

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class UnitCellWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="grid", **kwargs)
        self._changing_label = QLabel("Unit cell", parent=self._base)
        self._unit_label = QLabel("(nm)", parent=self._base)
        self._layout.addWidget(self._changing_label, 0, 0)
        self._layout.addWidget(self._unit_label, 1, 0)
        self._array_fields = {}
        self._configurator.update_trajectory_information()
        try:
            start_values = self._configurator._recommended_cell
        except AttributeError:
            start_values = self._configurator._default
        for row in range(3):
            for column in range(3):
                temp = QLineEdit(str(round(start_values[row][column], 5)), self._base)
                temp.setValidator(QDoubleValidator())
                self._layout.addWidget(temp, row, column + 1)
                self._array_fields[(row, column)] = temp
        self._mode = 0
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A new unit cell "
        for wid in self._array_fields.values():
            wid.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        array = 3 * [3 * [0]]
        for key, value in self._array_fields.items():
            try:
                array[(key[0], key[1])] = float(value.text())
            except:
                continue
        return array
