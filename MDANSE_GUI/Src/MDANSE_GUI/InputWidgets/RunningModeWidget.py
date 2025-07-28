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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QSpinBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class RunningModeWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._totalNumberOfProcessors = multiprocessing.cpu_count()
        self._last_numproc = None
        default_value = self._configurator.default
        self._value = default_value
        self.mode_box = QComboBox(self._base)
        self.mode_box.addItems(self._configurator.availablesModes)
        self.mode_box.setCurrentText(self._configurator.availablesModes[0])
        self._field = QSpinBox(self._base)
        self._field.setValue(1)
        self._field.setMinimum(1)
        self._field.setMaximum(multiprocessing.cpu_count())
        self._field.setEnabled(False)
        self._layout.addWidget(self.mode_box)
        self._layout.addWidget(self._field)
        self.mode_box.currentIndexChanged.connect(self.mode_changed)
        self._field.valueChanged.connect(self.numproc_changed)
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Choose if the job should run on one or more cores."
        for wid in [self._field, self.mode_box]:
            wid.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    @Slot()
    def mode_changed(self):
        mode = self.mode_box.currentText()
        if self._last_numproc is None:
            nextval = self._totalNumberOfProcessors
        else:
            nextval = self._last_numproc
        if mode == "single-core":
            self._field.setValue(1)
            self._field.setEnabled(False)
        else:
            self._field.setEnabled(True)
            self._field.setValue(nextval)

    @Slot()
    def numproc_changed(self):
        mode = self.mode_box.currentText()
        numproc = self._field.value()
        if mode == "single-core":
            return
        self._last_numproc = numproc

    def get_widget_value(self):
        mode = self.mode_box.currentText()
        numproc = self._field.value()
        if mode == "single-core":
            value = (mode,)
        else:
            value = (mode, numproc)
        return value
