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

from typing import TYPE_CHECKING, Literal

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from MDANSE_GUI.Tabs.Layouts.Panel import Panel

if TYPE_CHECKING:
    from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel


class DoublePanel(Panel):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._splitter = QSplitter(self._base)
        self._base_layout.addWidget(self._splitter)

        self._rightside = QWidget(self._base)
        self._rightlayout = QVBoxLayout(self._rightside)
        self._rightside.setLayout(self._rightlayout)

        # Reparent left/right side to scrolls
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidget(self._leftside)
        scroll_area_left.setWidgetResizable(True)

        scroll_area_right = QScrollArea()
        scroll_area_right.setWidget(self._rightside)
        scroll_area_right.setWidgetResizable(True)

        self._splitter.addWidget(scroll_area_left)
        self._splitter.addWidget(scroll_area_right)

        if self._view is not None:
            # Insert between upper/lower
            self._leftlayout.insertWidget(2, self._view)

        if self._visualiser is not None:
            self._rightlayout.addWidget(self._visualiser)
            if self._view is not None:
                self._view.connect_to_visualiser(self._visualiser)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 6)
