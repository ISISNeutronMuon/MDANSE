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

from PyQt6.QtGui import QFocusEvent
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QLineEdit

from MDANSE.Framework.Units import UNITS_MANAGER, Dims, UnitError, _Unit


class UnitLineEdit(QLineEdit):
    """Line edit for entering units."""
    def __init__(self, *args, dims: Dims, **kwargs):
        self.dims = dims
        super().__init__(*args, **kwargs)
        self.editingFinished.connect(self._check_unit)
        self._init_text = ""

    @Slot()
    def _check_unit(self):
        try:
            unit = _Unit.from_str(self.text())
        except UnitError:
            self.setText(self._init_text)
            return

        if unit.dimension != self.dims:
            self.setText(self._init_text)
            return

    def focusInEvent(self, a0: QFocusEvent | None) -> None:
        self._init_text = self.text()
        super().focusInEvent(a0)


class UnitComboBox(QComboBox):
    """Combo box for entering units."""
    def __init__(self, *args, dims: Dims, **kwargs):
        editor = super(*args, **kwargs)
        editor.setEditable(True)
        editor.setLineEdit(UnitLineEdit(dims=dims))
        editor.addItems(UNITS_MANAGER.filter_by_dimension(dims))
        editor.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)
