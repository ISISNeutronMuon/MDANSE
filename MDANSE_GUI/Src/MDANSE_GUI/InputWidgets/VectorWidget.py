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
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractScrollArea,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTableView,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase

if TYPE_CHECKING:
    from MDANSE.Framework.Parameters import Array, Vector


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

        val = np.atleast_2d(self.value)
        for row in val:
            items = [QStandardItem(str(elem)) for elem in row]
            self._model.appendRow(items)

        self.toggle_widgets()
        self._model.itemChanged.connect(self.updateValue)

    def get_widget_value(self) -> np.ndarray:
        return np.array(
            [
                [self.item(row, col) for col in range(self.columnCount())]
                for row in range(self.rowCount())
            ],
            dtype=float,
        ).reshape(self.parameter.shape)


class VectorWidget(WidgetBase[Vector]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._changing_label = QLabel("Vector", parent=self._base)
        self._layout.addWidget(self._changing_label)
        self._vector_fields = [
            QLineEdit(val, self._base) for val in map(str, self._configurator.default)
        ]

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The spatial properties in the analysis can be projected on a plane or on an axis, as chosen here."

        for field in self._vector_fields:
            self._layout.addWidget(field)
            field.setToolTip(tooltip_text)
        self._mode = 0
        self.updateValue()

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        try:
            vector = [float(x.text()) for x in self._vector_fields]
        except Exception:
            vector = [0, 0, 0]
        return vector
