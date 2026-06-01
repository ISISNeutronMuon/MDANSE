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

import multiprocessing
from typing import TYPE_CHECKING

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QSpinBox

from MDANSE.Framework.Parameters import RunningMode
from MDANSE_GUI.InputWidgets.ComboWidget import ComboWidget
from MDANSE_GUI.InputWidgets.IntegerWidget import IntegerWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class RunningModeWidget(WidgetBase[RunningMode]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._value = self.default

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Choose if the job should run on one or more cores."

        self.mode_box = ComboWidget(
            parent=self._base,
            label="Mode",
            tooltip=tooltip_text,
            configurable=self.parameter,
            prop="mode",
            parameter=self.parameter.descriptors["mode"],
        )

        self._field = IntegerWidget(
            parent=self._base,
            label="Number of cores",
            tooltip=tooltip_text,
            configurable=self.parameter,
            prop="n_procs",
            parameter=self.parameter.descriptors["n_procs"],
        )

        self.add_widget(self.mode_box, key="mode")
        self.add_widget(self._field, key="n_procs")

        self.mode_box.value_changed.connect(self.mode_changed)

        self.update_labels()
        self.mode_changed()

        self._field_map = {
            "mode": self.mode_box,
            "n_procs": self._field,
        }

    def trajectory_changed(self) -> None:
        """Nothing to do."""

    @Slot()
    def mode_changed(self):
        self._field._base.setEnabled(self.mode_box.value != "single-core")
        self.updateValue()

    def get_widget_value(self):
        mode = self.mode_box.value
        numproc = self._field.value

        return (mode, numproc)
