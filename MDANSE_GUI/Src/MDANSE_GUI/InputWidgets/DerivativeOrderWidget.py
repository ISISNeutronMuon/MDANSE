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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QLabel, QSpinBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase

suffix_dict = {
    "1": "st order",
    "2": "nd order",
    "3": "rd order",
    "4": "th order",
    "5": "th order",
}


class DerivativeOrderWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QHBoxLayout", **kwargs)
        self._field = QSpinBox(self._base)
        self._field.setMaximum(5)
        self._field.setMinimum(1)
        self._field.setValue(3)
        label = QLabel("Interpolation order", self._base)
        self.numerator = QLabel("st order")
        self.adjust_numerator_and_update(3)

        self._layout.addWidget(label)
        self._layout.addWidget(self._field)
        self._layout.addWidget(self.numerator)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The order of the polynomial function used for interpolating time-dependent variables."

        self._field.setToolTip(tooltip_text)
        self.numerator.setToolTip(tooltip_text)
        self._field.valueChanged.connect(self.adjust_numerator_and_update)

        for widget in self.parent()._widgets:
            if (
                widget._configurator
                is self._configurator.configurable[
                    self._configurator.dependencies["frames"]
                ]
            ):
                widget.value_changed.connect(self.updateValue)

    def configure_using_default(self):
        """This is too simple to have a default value"""

    def default_labels(self):
        if self._label_text == "":
            self._label_text = "DerivativeOrderWidget"
        if self._tooltip == "":
            self._tooltip = "The order of the polynomial function used for interpolating time-dependent variables."

    @Slot(int)
    def adjust_numerator_and_update(self, order: int):
        text_order = str(order)
        new_numerator = suffix_dict.get(text_order[-1])
        self.numerator.setText(new_numerator)
        self.updateValue()

    def get_widget_value(self):
        value = self._field.value()
        return value
