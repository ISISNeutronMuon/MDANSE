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

    @property
    def logged_things(self):
        return (self._view, self._visualiser, self._model)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._splitter = QSplitter(self._base)
        self._base_layout.addWidget(self._splitter)

        leftside = QWidget(self._base)
        scroll_area_left = QScrollArea()
        scroll_area_left.setWidget(leftside)
        scroll_area_left.setWidgetResizable(True)
        leftlayout = QVBoxLayout(leftside)
        leftside.setLayout(leftlayout)

        rightside = QWidget(self._base)
        scroll_area_right = QScrollArea()
        scroll_area_right.setWidget(rightside)
        scroll_area_right.setWidgetResizable(True)
        rightlayout = QVBoxLayout(rightside)
        rightside.setLayout(rightlayout)

        self._splitter.addWidget(scroll_area_left)
        self._splitter.addWidget(scroll_area_right)

        upper_buttons = QWidget(leftside)
        ub_layout = QHBoxLayout(upper_buttons)
        upper_buttons.setLayout(ub_layout)
        lower_buttons = QWidget(leftside)
        lb_layout = QHBoxLayout(lower_buttons)
        lower_buttons.setLayout(lb_layout)

        self._tab_label = QLabel(leftside)
        leftlayout.addWidget(self._tab_label)
        leftlayout.addWidget(upper_buttons)

        if self._view is not None:
            leftlayout.addWidget(self._view)

        leftlayout.addWidget(lower_buttons)

        self._leftlayout = leftlayout
        self._rightlayout = rightlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout

        if self._visualiser is not None:
            self._rightlayout.addWidget(self._visualiser)
            if self._view is not None:
                self._view.connect_to_visualiser(self._visualiser)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 2)

    def current_item(self):
        try:
            index = self._view.currentIndex()
            item = self._model.itemFromIndex(index)
        except Exception as e:
            self.error.emit(repr(e))
        else:
            return item
