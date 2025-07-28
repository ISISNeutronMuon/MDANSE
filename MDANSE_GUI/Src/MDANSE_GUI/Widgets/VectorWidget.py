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

from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal, Slot
from qtpy.QtGui import QDoubleValidator, QIntValidator
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class VectorWidget(QWidget):
    value_changed = Signal(list)

    def __init__(self, *args, dtype=None, **kwargs) -> None:
        label_text = kwargs.pop("label", "Vector input")
        super().__init__(*args, **kwargs)
        if dtype == "int":
            self._dtype = "int"
        else:
            self._dtype = "float"
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(QLabel(label_text, self))
        self._fields = []
        for _ in range(3):
            temp = QLineEdit(self)
            if self._dtype == "int":
                temp.setValidator(QIntValidator())
                temp.setText("0")
            elif self._dtype == "float":
                temp.setValidator(QDoubleValidator())
                temp.setText("0.0")
            self._fields.append(temp)
            layout.addWidget(temp)
        self.collect_values()
        for temp in self._fields:
            temp.textChanged.connect(self.collect_values)

    @Slot()
    def collect_values(self):
        result = []
        for temp in self._fields:
            strvalue = temp.text()
            if self._dtype == "int":
                value = int(strvalue)
            elif self._dtype == "float":
                value = float(strvalue)
            result.append(value)
        self._value = result
        self.value_changed.emit(result)

    def setText(self, input_string: str):
        if self._dtype == "int":
            converter = int
        elif self._dtype == "float":
            converter = float
        try:
            self.set_value(
                [converter(x) for x in input_string.strip("[]()").split(",")]
            )
        except Exception:
            self.set_value([0, 0, 0])

    def text(self):
        return ",".join([field.text() for field in self._fields])

    @Slot(object)
    def set_value(self, new_value):
        for n, value in enumerate(new_value):
            self._fields[n].setText(str(value))
