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
from __future__ import annotations

from qtpy.QtCore import QObject, QTimer, Signal, Slot
from qtpy.QtWidgets import QPushButton


class DelayedButton(QPushButton):
    needs_updating = Signal()

    def __init__(self, *args, **kwargs):
        delay_time = kwargs.pop("delay", 1000)
        inactive_message = kwargs.pop("inactive_text", "Starting...")
        super().__init__(*args, **kwargs)

        self._delay_time = delay_time
        self._inactive_message = inactive_message
        self._freeze_updates = False
        self._active_message = self.text()
        self.clicked.connect(self.start_delay)

    def setEnabled(self, a0: bool) -> None:
        if not self._freeze_updates:
            return super().setEnabled(a0)

    @Slot()
    def start_delay(self):
        self.setText(self._inactive_message)
        self.setEnabled(False)
        self._freeze_updates = True
        QTimer.singleShot(self._delay_time, self.end_delay)

    @Slot()
    def end_delay(self):
        self.setText(self._active_message)
        self._freeze_updates = False
        self.needs_updating.emit()
