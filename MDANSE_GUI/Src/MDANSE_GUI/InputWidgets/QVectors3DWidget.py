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

from qtpy.QtGui import QStandardItemModel
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

        default = self._configurator.default

        self._view = QTableView(self._base)
        self._model = QStandardItemModel(10, 3)
        self._view.setModel(self._model)
        self._layout.addWidget(self._view)

        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()
        self._view.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents,
        )
