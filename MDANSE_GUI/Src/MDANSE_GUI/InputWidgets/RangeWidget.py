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

from qtpy.QtGui import QDoubleValidator, QIntValidator
from qtpy.QtWidgets import QLabel, QLineEdit

from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class RangeWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        self.setup_fields(*args, **kwargs)

    def setup_fields(self, *args, **kwargs):
        start, end, step = kwargs.get("default", self._configurator.default)
        num_type = kwargs.get("valueType", int)

        labels = [
            QLabel("From", self._base),
            QLabel("to", self._base),
            QLabel("in steps of", self._base),
        ]
        fields = [
            QLineEdit(str(num_type(start)), self._base),
            QLineEdit(str(num_type(end)), self._base),
            QLineEdit(str(num_type(step)), self._base),
        ]
        placeholders = [str(num_type(start)), str(num_type(end)), str(num_type(step))]
        if num_type is int:
            validators = [QIntValidator(parent_field) for parent_field in fields]
        else:
            validators = [QDoubleValidator(parent_field) for parent_field in fields]
        for field_num in range(3):
            self._layout.addWidget(labels[field_num], 0, 2 * field_num)
            self._layout.addWidget(fields[field_num], 0, 2 * field_num + 1)
            fields[field_num].setValidator(validators[field_num])
            fields[field_num].textChanged.connect(self.updateValue)
            fields[field_num].setPlaceholderText(placeholders[field_num])
        self._fields = fields
        self._validators = validators
        self._num_type = num_type
        self._default_values = placeholders
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Values to be used, given as (First, Last, StepSize)"
        for wid in fields + labels:
            wid.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "RangeWidget"
        if self._tooltip == "":
            self._tooltip = "Values to be used, given as (First, Last, StepSize)"

    def value_from_configurator(self):
        if self._configurator.check_dependencies():
            minval, maxval = self._configurator.mini, self._configurator.maxi
            LOG.info(f"Configurator min/max: {minval}, {maxval}")
            if maxval is None:
                return
            for val in self._validators:
                val.setBottom(-abs(maxval))
                val.setTop(abs(maxval))

    def get_widget_value(self):
        result = []
        for n, field in enumerate(self._fields):
            strval = field.text()
            try:
                val = self._num_type(strval)
            except Exception:
                val = self._num_type(self._default_values[n])
            result.append(val)
        return result
