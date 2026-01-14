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

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from MDANSE_GUI.Tabs.Layouts.Panel import Panel


class SinglePanel(Panel):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self._base)
        scroll_area.setWidgetResizable(True)
        self._base_layout.addWidget(scroll_area)

        leftside = QWidget(self._base)
        leftlayout = QVBoxLayout(leftside)
        leftside.setLayout(leftlayout)

        self._layout.addWidget(leftside)

        upper_buttons = QWidget(leftside)
        ub_layout = QHBoxLayout(upper_buttons)
        upper_buttons.setLayout(ub_layout)
        lower_buttons = QWidget(leftside)
        lb_layout = QHBoxLayout(lower_buttons)
        lower_buttons.setLayout(lb_layout)

        self._tab_label = QLabel(leftside)
        leftlayout.addWidget(self._tab_label)
        leftlayout.addWidget(upper_buttons)
        leftlayout.addWidget(lower_buttons)

        if self._visualiser is not None:
            leftlayout.addWidget(self._visualiser)

        self._leftlayout = leftlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout
