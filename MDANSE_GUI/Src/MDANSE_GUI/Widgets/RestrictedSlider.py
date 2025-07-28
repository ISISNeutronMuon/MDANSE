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
from qtpy.QtWidgets import QSlider


class RestrictedSlider(QSlider):
    new_limit = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._lower_limit = None
        self._upper_limit = None
        self._coupled = False

    @Slot(object)
    def set_lower_limit(self, new_limit: int):
        if not self._coupled:
            return
        self._lower_limit = new_limit
        if new_limit is None:
            return
        if self.value() < new_limit:
            self.setValue(new_limit)

    @Slot(object)
    def set_upper_limit(self, new_limit: int):
        if not self._coupled:
            return
        self._upper_limit = new_limit
        if new_limit is None:
            return
        if self.value() > new_limit:
            self.setValue(new_limit)

    def setValue(self, a0: int) -> None:
        if not self._coupled:
            return super().setValue(a0)
        if self._upper_limit is not None:
            if a0 > self._upper_limit:
                return
        if self._lower_limit is not None:
            if a0 < self._lower_limit:
                return
        self.new_limit.emit(a0)
        return super().setValue(a0)
