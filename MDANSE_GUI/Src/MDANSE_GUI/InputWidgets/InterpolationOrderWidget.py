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
    "0": "th order - no interpolation",
    "1": "st order",
    "2": "nd order",
    "3": "rd order",
    "4": "th order",
    "5": "th order",
}


class InterpolationOrderWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QHBoxLayout", **kwargs)
        _source_object = kwargs.get("source_object", None)

        self._field = QSpinBox(self._base)
        self._field.setMaximum(5)
        configurator = self._configurator
        trajectory = configurator.configurable[configurator.dependencies["trajectory"]][
            "instance"
        ]
        label = QLabel("Interpolation order", self._base)
        self.numerator = QLabel("st order")
        if not trajectory.has_variable("velocities"):
            self._field.setMinimum(1)
            self._field.setValue(3)
            self.adjust_numerator_and_update(3)
        else:
            self._field.setMinimum(0)
            self._field.setValue(0)
            self.adjust_numerator_and_update(0)

        self._layout.addWidget(label)
        self._layout.addWidget(self._field)
        self._layout.addWidget(self.numerator)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The order of the polynomial function used for interpolating velocity values from atom positions. If zero, velocity values present in the trajectory will be used."
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
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "InterpolationOrderWidget"
        if self._tooltip == "":
            self._tooltip = "The order of the polynomial function used for interpolating velocity values from atom positions. If zero, velocity values present in the trajectory will be used."

    @Slot(int)
    def adjust_numerator_and_update(self, order: int):
        text_order = str(order)
        new_numerator = suffix_dict.get(text_order[-1], " - no interpolation")
        self.numerator.setText(new_numerator)
        self.updateValue()

    def get_widget_value(self):
        value = self._field.value()

        return value
