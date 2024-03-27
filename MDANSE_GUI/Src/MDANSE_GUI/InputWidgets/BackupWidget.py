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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

from icecream import ic
from qtpy.QtWidgets import QLineEdit
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class BackupWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        self._field = QLineEdit(str(self._configurator.default))
        self._field.setPlaceholderText(str(self._configurator.default))
        self._layout.addWidget(self._field)
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "There should have been a specialised widget for this parameter, but there isn't."
        self._field.textChanged.connect(self.updateValue)
        self._field.setToolTip(tooltip_text)
        self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        temp_text = self._field.text().strip()
        if temp_text == "None" or temp_text == "":
            result = str(self._configurator.default)
            self._empty = True
        else:
            result = temp_text
            self._empty = False
        return result
