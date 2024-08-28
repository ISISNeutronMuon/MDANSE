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

from typing import Optional, List

import numpy as np
from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTextEdit,
)
from qtpy.QtCore import Signal, Slot, QObject

from MDANSE.Framework.Jobs.IJob import IJob


class DataDialog(QDialog):
    new_style = Signal(str)
    icon_swap = Signal(bool)

    def __init__(
        self,
        *args,
        input_data: List[np.ndarray],
        input_units: List[str],
        is_input=False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._data = input_data

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        top_layout = QHBoxLayout()
        layout.addChildLayout(top_layout)
        self._input_units = input_units
        self._unit_boxes = [QComboBox(self), QComboBox(self), QComboBox(self)]
        for box in self._unit_boxes:
            top_layout.addWidget(box)
        self._display = QTextEdit(self)
        layout.addWidget(self._display)
        if is_input:
            self._confirm = QPushButton("Apply", self)
            self._confirm.clicked.connect(self.commitChanges)
            layout.addWidget(self._confirm)

    def commitChanges(self):
        text = self._display.document().toPlainText()
        self.new_style.emit(text)
        label = self._selector.currentText()
        if "dark" in label:
            self.icon_swap.emit(True)
        else:
            self.icon_swap.emit(False)
