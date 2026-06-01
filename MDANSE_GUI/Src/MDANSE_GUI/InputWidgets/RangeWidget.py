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

from collections.abc import Sequence
from typing import TYPE_CHECKING

from more_itertools import numeric_range
from qtpy.QtWidgets import QDoubleSpinBox, QLabel, QSpinBox, QWidget

from MDANSE.Framework.Parameters import NumericRange, Range
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class RangeWidget(WidgetBase[Range]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)

        box_type = QSpinBox if self.parameter.dtype is int else QDoubleSpinBox

        self._labels = []
        self._fields = []
        labels = ("Start", "Stop", "Step")

        tooltip_text = (
            self._tooltip or "Values to be used, given as (First, Last, StepSize)"
        )

        # Label takes position 0 in QWidget
        shift = isinstance(self._base, QWidget)

        for i, label_name in enumerate(labels):
            label = QLabel(label_name, self._base)
            field = box_type(self._base)

            field.setToolTip(tooltip_text)
            field.valueChanged.connect(self.updateValue)

            self._labels.append(label)
            self._fields.append(field)

            self._layout.addWidget(label, 0, 2 * i + shift)
            self._layout.addWidget(field, 0, 2 * i + 1 + shift)

        self.trajectory_changed()
        self.default_labels()
        self.update_labels()
        self.toggle_widgets()
        self.updateValue()

    def set_value(self, value: Sequence[int]) -> None:
        if len(value) != 3:
            raise ValueError(f"Expected start, stop, step, received: {len(value)}.")

        with block_signals(self):
            for field, elem in zip(self._fields, value, strict=True):
                field.setValue(elem)

        self.updateValue()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "RangeWidget"
        if not self._tooltip:
            self._tooltip = "Values to be used, given as (First, Last, StepSize)"

    def trajectory_changed(self) -> None:
        if not self.ranges:
            for field in self._fields:
                field.setEnabled(True)
                field.setRange(None, None)

            return

        match self.ranges:
            case _ if self.default != "N/A":
                if isinstance(self.default, (NumericRange, range)):
                    defaults = self.default.start, self.default.stop, self.default.step
                elif isinstance(self.default, numeric_range):
                    defaults = (
                        self.default._start,
                        self.default._stop,
                        self.default._step,
                    )
                else:
                    defaults = self.default
            case (None, None):
                defaults = (0, -1, 1)
            case (mini, None):
                defaults = (mini, -1, 1)
            case (None, maxi):
                defaults = (0, maxi, 1)
            case (mini, maxi) if self.parameter.dtype is not int:
                step = round((maxi - mini) / 100, 2)
                defaults = (mini, maxi, step)
            case (mini, maxi):
                defaults = (mini, maxi, 1)
            case _:
                raise NotImplementedError(f"Unable to handle {self.ranges=}")

        mini, maxi = self.ranges

        for field, val in zip(self._fields, defaults, strict=True):
            field.setValue(val)
            field.setEnabled(True)
            field.setSingleStep(defaults[2])
            if mini is not None:
                field.setMinimum(mini)
            if maxi is not None:
                field.setMaximum(maxi)

    def get_widget_value(self):
        values = [field.value() for field in self._fields]
        if self.parameter.include_last:
            values[1] -= values[2]  # Include last

        return tuple(values)
