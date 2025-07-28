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

from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import QCheckBox, QDoubleSpinBox, QLineEdit

from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class OptionalFloatWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_option = float(self._configurator.default[1])
        except ValueError:
            default_option = 0.0
        label_text = self._configurator.label_text
        self._apply_box = QCheckBox(label_text, self._base)
        self._apply_box.setTristate(False)
        self._apply_box.checkStateChanged.connect(self.toggle_widgets)
        self._apply_box.setChecked(False)
        if self._configurator.choices:
            field = QDoubleSpinBox(self._base)
            field.setMinimum(self._configurator.choices[0])
            field.setMaximum(self._configurator.choices[-1])
            if len(self._configurator.choices) > 1:
                field.setSingleStep(
                    self._configurator.choices[1] - self._configurator.choices[0]
                )
            field.setValue(default_option)
        else:
            field = QLineEdit(self._base)
            validator = QDoubleValidator(field)
            minval, maxval = self._configurator.mini, self._configurator.maxi
            if minval is not None:
                validator.setBottom(minval)
            if maxval is not None:
                validator.setTop(maxval)
            field.setValidator(validator)
            field.setText(str(default_option))
            field.textChanged.connect(self.updateValue)
            field.setPlaceholderText(str(default_option))
        field.setToolTip(self._tooltip)
        self._layout.addWidget(self._apply_box)
        self._layout.addWidget(field)
        self._field = field
        self._default_value = default_option
        self.default_labels()
        self.update_labels()
        self._field.setEnabled(False)
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single floating-point number"
        field.setToolTip(tooltip_text)

    @Slot()
    def toggle_widgets(self):
        if self._apply_box.checkState() == Qt.CheckState.Checked:
            self._field.setEnabled(True)
        else:
            self._field.setEnabled(False)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "FloatWidget"
        if self._tooltip == "":
            self._tooltip = "A single floating-point number"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        flag = self._apply_box.checkState() == Qt.CheckState.Checked
        if not flag:
            return [False, self._default_value]
        strval = self._field.text().strip()
        if len(strval) < 1:
            strval = self._default_value
        return [True, strval]

    def configure_using_default(self):
        """Makes the configurator use its default value, and highlights it
        in the GUI"""
        default = self._configurator.default
        LOG.info(f"Setting {default} as placeholder text")
        self._field.setPlaceholderText(str(self._default_value))
        self._configurator.configure(default)
