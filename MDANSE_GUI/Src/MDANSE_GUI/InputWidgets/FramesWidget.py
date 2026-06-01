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

import traceback
from collections.abc import Sequence
from typing import TYPE_CHECKING

from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import QLabel, QSpinBox

from MDANSE.Framework.Parameters import FrameSelect
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class FramesWidget(WidgetBase[FrameSelect]):
    def __init__(
        self,
        *args,
        layout_type: None = None,
        **kwargs,
    ):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)

        self._labels = []
        self._fields = []

        labels = ("First frame", "Last frame", "in steps of")

        tooltip_text = self._tooltip or "Frames to use (inclusive)."

        for i, label_name in enumerate(labels):
            label = QLabel(label_name, self._base)
            field = QSpinBox(self._base)

            field.setToolTip(tooltip_text)
            field.valueChanged.connect(self.updateValue)

            self._labels.append(label)
            self._fields.append(field)

            self._layout.addWidget(label, 0, 2 * i)
            self._layout.addWidget(field, 0, 2 * i + 1)

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
            self._label_text = "FramesWidget"
        if not self._tooltip:
            self._tooltip = (
                "Trajectory frames to be used, given as (First, Last, StepSize)"
            )

    def trajectory_changed(self) -> None:
        mini, maxi = self.ranges
        maxi -= 2
        defaults = [
            default if default is not None else std_default
            for default, std_default in zip((mini, maxi, 1), (0, -1, 1), strict=True)
        ]

        for field, val in zip(self._fields, defaults, strict=True):
            field.setValue(val)
            limit = maxi if maxi is not None else 0
            field.setEnabled(True)
            field.setRange(-limit, limit)

    def get_widget_value(self):
        values = [field.value() for field in self._fields]
        values[1] += 1  # Include last
        return tuple(values)
