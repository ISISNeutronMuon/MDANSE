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

import math

from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import QLabel, QLineEdit

from .FramesWidget import FramesWidget


class CorrelationFramesWidget(FramesWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self._last_frame <= 0:
            c_frames = "1"
        else:
            c_frames = str(math.ceil(self._last_frame * 0.5))
        field = QLineEdit(c_frames, self._base)
        validator = QIntValidator(field)

        field.setValidator(validator)
        field.textChanged.connect(self.updateValue)
        field.setPlaceholderText(c_frames)

        self._layout.addWidget(QLabel("Correlation frames", self._base), 1, 0)
        self._layout.addWidget(field, 1, 1)

        self._fields.append(field)
        self._validators.append(QIntValidator(field))
        self._default_values.append(c_frames)
