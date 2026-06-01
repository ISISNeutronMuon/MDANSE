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

import sys
from typing import TYPE_CHECKING, SupportsInt

from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import QCheckBox, QLineEdit, QSpinBox

from MDANSE.Framework.Parameters import Integer
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class IntegerWidget(WidgetBase[Integer]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._field = QSpinBox(self._base)

        if self.choices:
            self.reset_choices()
        elif self.ranges:
            self.reset_ranges()

        self.set_value(self.default)

        self._layout.addWidget(self._field)

        self.default_labels()
        self.update_labels()
        self.toggle_widgets()
        self.updateValue()

    @Slot()
    def reset_choices(self) -> None:
        choices = self.choices
        self._field.setMinimum(min(choices))
        self._field.setMaximum(max(choices))

    @Slot()
    def reset_ranges(self) -> None:
        mini, maxi = self.ranges
        if mini is not None:
            self._field.setMinimum(mini)
        else:
            self._field.setMinimum(-(2**31) + 2)
        if maxi is not None:  # Range exclusive.
            self._field.setMaximum(maxi - 1)
        else:
            self._field.setMaximum(2**31 - 1)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "IntegerWidget"
        if not self._tooltip:
            self._tooltip = "A single integer number"

    def set_value(self, value: SupportsInt | None) -> None:
        if self.parameter.optional and value is None:
            self._apply_box.setChecked(False)
            return

        self._field.setValue(int(value))
        self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        return self._field.value()
