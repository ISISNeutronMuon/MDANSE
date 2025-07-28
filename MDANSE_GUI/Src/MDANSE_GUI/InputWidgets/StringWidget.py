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

from qtpy.QtWidgets import QLineEdit

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class StringWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_option = self._configurator.default
        field = QLineEdit(self._base)
        field.setText(default_option)
        field.setPlaceholderText(default_option)
        field.textChanged.connect(self.updateValue)
        field.setToolTip(self._tooltip)
        self._field = field
        self._default_value = default_option
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A text string variable. When in doubt, erase the text to see the example (placeholder) text"
        field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "StringWidget"
        if self._tooltip == "":
            self._tooltip = "A text string variable. When in doubt, erase the text to see the example (placeholder) text"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text().strip()
        if len(strval) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return strval

    def configure_using_default(self):
        default = self._configurator.default
        self._field.setPlaceholderText(default)
        self._configurator.configure(default)
