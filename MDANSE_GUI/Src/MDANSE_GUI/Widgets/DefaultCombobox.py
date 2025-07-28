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

if TYPE_CHECKING:
    from qtpy.QtWidgets import QComboBox


def highlight_default_value(field: QComboBox) -> None:
    """Takes the input QComboBox widget and changes the font of the currently
    selected item to bold typeface. This is meant to indicate to the users
    which option was originally selected.

    Parameters
    ----------
    field : QComboBox
        The changes will be applied to the data model of this input widget
    """
    model = field.model()
    row = field.currentIndex()
    item = model.item(row, 0)
    newfont = item.font()
    newfont.setBold(True)
    item.setFont(newfont)
