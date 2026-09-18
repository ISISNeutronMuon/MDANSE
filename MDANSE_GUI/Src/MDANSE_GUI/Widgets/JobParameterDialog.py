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

from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.IJob import IJob


class MatchingEntriesLine(QWidget):
    def __init__(
        self,
        *args,
        name: str = "Entry",
        current_value: str = "",
        new_value: str = "",
        use_it: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        self.label = QLabel(name, self)
        self.key = name
        self.value = new_value
        self.newval_line = QLineEdit(str(new_value), self)
        currentval_line = QLineEdit(current_value, self)
        self.use_checkbox = QCheckBox("Replace", self)
        self.use_checkbox.setChecked(True)
        for widget in [
            self.label,
            self.newval_line,
            self.use_checkbox,
            currentval_line,
        ]:
            layout.addWidget(widget)
        self.setLayout(layout)


class JobParameterDialog(QDialog):
    def __init__(
        self,
        *args,
        current_parameters: dict[str, Any],
        new_parameters: dict[str, Any],
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.is_accepted = False
        layout = QVBoxLayout(self)
        incoming_keys = set(new_parameters.keys())
        existing_keys = set(current_parameters.keys())
        matches = incoming_keys.intersection(existing_keys)
        missing = incoming_keys.difference(existing_keys)
        self.ok_button = QPushButton("Accept values", self)
        self.ok_button.clicked.connect(self.accept_values)
        self.match_lines = []
        for key in matches:
            line = MatchingEntriesLine(
                self,
                name=key,
                current_value=str(current_parameters[key]),
                new_value=new_parameters[key],
                use_it=True,
            )
            layout.addWidget(line)
            self.match_lines.append(line)
        layout.addWidget(
            QLabel(
                "The file contained the following parameters that will not be used:",
                self,
            )
        )
        layout.addWidget(QLineEdit(", ".join([str(x) for x in missing]), self))
        layout.addWidget(self.ok_button)

    def accept_values(self):
        self.is_accepted = True
        self.close()

    def get_results(self) -> dict[str, Any]:
        if not self.is_accepted:
            return {}
        result = {}
        for line in self.match_lines:
            if line.use_checkbox.isChecked():
                result[line.key] = line.value
        return result
