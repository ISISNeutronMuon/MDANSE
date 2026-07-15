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

import ast

from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractScrollArea,
    QSizePolicy,
    QTableView,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class QVectors3DWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        self._relative_size = 3

        default = self._configurator._default
        self.configurators = self._configurator._configurators_classes

        self._view = QTableView(self._base)

        self._model = QStandardItemModel(9, 3)
        for i, (key, val) in enumerate(default.items()):
            item = QStandardItem(key)
            item.setEditable(False)
            self._model.setItem(i, 0, item)

            self._model.setItem(i, 1, QStandardItem(str(val)))

            item = QStandardItem(self.configurators[key].func.__name__)
            item.setEditable(False)
            self._model.setItem(i, 2, item)

        self._view.setModel(self._model)
        self._layout.addWidget(self._view)

        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()
        self._view.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents,
        )

        self._model.itemChanged.connect(self.updateValue)

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        settings = {}
        for row in range(self._model.rowCount()):
            key = self._model.item(row, 0).text()
            val_item = self._model.item(row, 1)
            val = val_item.text()
            configurator_name = self._model.item(row, 2).text()

            if configurator_name in ("RangeConfigurator", "VectorConfigurator"):
                settings[key] = val
                try:
                    val = ast.literal_eval(val)
                except (SyntaxError, ValueError):
                    val_item.setData(
                        QBrush(Qt.GlobalColor.red),
                        role=Qt.ItemDataRole.BackgroundRole,
                    )
                    continue

            configurator = self.configurators[key](key)
            configurator.configure(val)
            if configurator.error_status == "OK":
                val_item.setData(0, role=Qt.ItemDataRole.BackgroundRole)
            else:
                val_item.setData(
                    QBrush(Qt.GlobalColor.red),
                    role=Qt.ItemDataRole.BackgroundRole,
                )

            settings[key] = val

        return settings
