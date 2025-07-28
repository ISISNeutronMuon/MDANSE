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

from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import QLineEdit, QSpinBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class IntegerWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_option = int(self._configurator.default)
        except ValueError:
            default_option = 0
        if self._configurator.choices:
            field = QSpinBox(self._base)
            field.setMinimum(self._configurator.choices[0])
            field.setMaximum(self._configurator.choices[-1])
            field.setValue(default_option)
        else:
            field = QLineEdit(self._base)
            validator = QIntValidator(field)
            minval, maxval = self._configurator.mini, self._configurator.maxi
            if minval is not None:
                validator.setBottom(minval)
            if maxval is not None:
                validator.setTop(maxval)
            field.setValidator(validator)
            field.setText(str(default_option))
            field.setPlaceholderText(str(default_option))
            field.textChanged.connect(self.updateValue)
        self._field = field
        self._default_value = default_option
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single integer number"
        field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "IntegerWidget"
        if self._tooltip == "":
            self._tooltip = "A single integer number"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text().strip()
        if len(strval) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return strval
