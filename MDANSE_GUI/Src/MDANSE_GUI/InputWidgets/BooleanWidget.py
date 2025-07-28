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

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QCheckBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class BooleanWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_option = self._configurator.default
        field = QCheckBox(self._base)
        field.setTristate(False)
        field.setChecked(default_option)
        field.stateChanged.connect(self.updateValue)
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        field.setToolTip(tooltip_text)
        self._field = field
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()
        self.updateValue()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "BooleanWidget"
        if self._tooltip == "":
            self._tooltip = "A single logical value that can be True of False"
        self._field.setToolTip(self._tooltip)

    def configure_using_default(self):
        """No need to anything for Boolean"""

    def get_widget_value(self):
        return self._field.checkState() == Qt.CheckState.Checked
