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

from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import QCheckBox, QDoubleSpinBox, QLineEdit

from MDANSE.Framework.Parameters import Float
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class FloatWidget(WidgetBase[Float]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._field = QDoubleSpinBox(self._base)

        if self.parameter.choices:
            self._field.setMinimum(min(self.parameter.choices))
            self._field.setMaximum(max(self.parameter.choices))
            if len(self._configurator.choices) > 1:
                self._field.setSingleStep(
                    self._configurator.choices[1] - self._configurator.choices[0]
                )
        else:
            if self.parameter.minimum is not None:
                self._field.setMinimum(self.parameter.minimum)
            if self.parameter.maximum is not None:
                self._field.setMaximum(self.parameter.maximum)

        if self.parameter.optional and self.default is None:
            pass
        elif self.default != "N/A":
            self._field.setValue(self.default)
        else:
            self._field.setValue(0.0)

        self._layout.addWidget(self._field)
        self.default_labels()
        self.update_labels()
        self.toggle_widgets()
        self.updateValue()
        tooltip_text = self._tooltip or "A single floating-point number"

        self._field.valueChanged.connect(self.updateValue)
        self._field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "FloatWidget"
        if not self._tooltip:
            self._tooltip = "A single floating-point number"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        return self._field.value()
