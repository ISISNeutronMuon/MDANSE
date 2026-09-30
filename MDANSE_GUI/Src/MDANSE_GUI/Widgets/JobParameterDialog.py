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
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.IJob import IJob


def create_matching_line(
    parent: QWidget,
    name: str = "Entry",
    current_value: str = "",
    new_value: str = "",
    use_it: bool = True,
) -> tuple[QLabel, QTextBrowser, QCheckBox, QTextBrowser]:
    """Create widgets for one entry from the parameter dictionary.

    Parameters
    ----------
    parent : QWidget
        Parent object for the new widgets.
    name : str, optional
        Name of the input parameter, by default "Entry",
    current_value : str, optional
        Value stored by the IJob at the moment, by default "".
    new_value : str, optional
        Value imported from the file, by default "".
    use_it : bool, optional
        True if the checkbox should start off already checked, by default True.

    Returns
    -------
    tuple[QLabel, QTextBrowser, QCheckBox, QTextBrowser]
        Name label, new value as text, use-it checkbox, current value as text.
    """
    label = QLabel(name, parent)
    newval_line = QTextBrowser(parent)
    currentval_line = QTextBrowser(parent)
    newval_line.setText(str(new_value))
    currentval_line.setText(current_value)
    use_checkbox = QCheckBox("Replace", parent)
    use_checkbox.setChecked(use_it)
    newval_line.setReadOnly(True)
    currentval_line.setReadOnly(True)
    return (label, newval_line, use_checkbox, currentval_line)


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
        layout = QGridLayout(self)
        incoming_keys = set(new_parameters.keys())
        existing_keys = set(current_parameters.keys())
        matches = incoming_keys.intersection(existing_keys)
        missing = incoming_keys.difference(existing_keys)
        self.ok_button = QPushButton("Accept values", self)
        self.ok_button.clicked.connect(self.accept_values)
        self.match_lines = []
        layout.addWidget(QLabel("Variable name", self), 0, 0)
        layout.addWidget(QLabel("New value", self), 0, 1)
        layout.addWidget(QLabel("Replace value?", self), 0, 2)
        layout.addWidget(QLabel("Current value", self), 0, 3)
        for row_num, key in enumerate(matches):
            label, left_text, checkbox, right_text = create_matching_line(
                self,
                name=key,
                current_value=str(current_parameters[key]),
                new_value=new_parameters[key],
                use_it=True,
            )
            layout.addWidget(label, row_num + 1, 0)
            layout.addWidget(left_text, row_num + 1, 1)
            layout.addWidget(checkbox, row_num + 1, 2)
            layout.addWidget(right_text, row_num + 1, 3)
            self.match_lines.append((key, checkbox, new_parameters[key]))
        last_row = len(matches) + 1
        layout.addWidget(
            QLabel(
                "The file contained the following parameters that will not be used:",
                self,
            ),
            last_row,
            0,
            1,
            4,
        )
        missing_parameters_box = QTextBrowser(self)
        missing_parameters_box.setText(", ".join([str(x) for x in missing]))
        missing_parameters_box.setReadOnly(True)
        layout.addWidget(missing_parameters_box, last_row + 1, 0, 1, 4)
        layout.addWidget(self.ok_button, last_row + 2, 1, 1, 2)

    def accept_values(self):
        self.is_accepted = True
        self.close()

    def get_results(self) -> dict[str, Any]:
        if not self.is_accepted:
            return {}
        result = {}
        for key, checkbox, new_value in self.match_lines:
            if checkbox.isChecked():
                result[key] = new_value
        return result
