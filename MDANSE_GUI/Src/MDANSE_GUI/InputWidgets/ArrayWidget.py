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

from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QAbstractScrollArea, QSizePolicy, QTableView

from MDANSE.Framework.Parameters import Array, Vector
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class ArrayWidget(WidgetBase[Array | Vector]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._view = QTableView(self._base)
        self._model = QStandardItemModel(self._base)

        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setModel(self._model)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()
        self._view.verticalHeader().hide()
        self._view.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )

        if len(self.parameter.shape) > 2:
            raise NotImplementedError("3D data objects not supported")

        val = self.value if self.value is not None else np.zeros(self.parameter.shape)

        for row in np.atleast_2d(val):
            items = [QStandardItem(str(elem)) for elem in row]
            self._model.appendRow(items)

        self._layout.addWidget(self._view)
        self.toggle_widgets()
        self._model.itemChanged.connect(self.updateValue)

    def set_value(self, val: npt.NDArray[np.floating]) -> None:
        if val.shape != self.parameter.shape:
            raise ValueError(
                "Shape mismatch: \n"
                f"expected: {self.parameter.shape}\n"
                f"received: {val.shape}"
            )

        with block_signals(self._model):
            for (row, col), elem in np.ndenumerate(val):
                self._model.item(row, col).setText(str(elem))

        self.updateValue()

    @Slot()
    def toggle_widgets(self) -> None:
        if not self.parameter.optional:
            return

        self._view.setEnabled(self._apply_box.checkState() != Qt.CheckState.Checked)
        self.updateValue()
