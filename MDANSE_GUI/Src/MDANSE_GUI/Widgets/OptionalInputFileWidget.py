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
from qtpy.QtWidgets import QPushButton

from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget


class OptionalInputFileWidget(InputFileWidget):
    """Optional file doesn't need to care if underlying file is valid until you try to load."""

    def __init__(self, *args, button_label: str, **kwargs):
        self.button_label = button_label
        super().__init__(*args, **kwargs)

    def add_widgets_to_layout(self):
        super().add_widgets_to_layout()

        button = QPushButton(self.button_label, self._base)
        button.clicked.connect(self.load_file)
        self._layout.addWidget(button)

    def load_file(self):
        current_value = self.get_widget_value()
        if self._empty:
            self.clear_error()
            return

        try:
            self._configurator.configure(current_value)
        except Exception:
            self.mark_error(
                "COULD NOT SET THIS VALUE - you may need to change the values in other widgets"
            )
        self.value_changed.emit()
        if self._configurator.valid:
            self.clear_error()
            self.value_updated.emit()
        else:
            self.mark_error(self._configurator.error_status)

    @Slot()
    def updateValue(self):
        pass
