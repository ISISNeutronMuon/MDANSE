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


class SinglePanel(QWidget):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    error = Signal(str)
    item_picked = Signal(object)

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self._visualiser = None

        visualiser_side = kwargs.pop("visualiser_side", None)
        self._tab_reference = kwargs.pop("tab_reference", None)
        _ = kwargs.pop("data_side", None)

        super().__init__(*args, **kwargs)

        buffer = QWidget(self)
        scroll_area = QScrollArea()
        scroll_area.setWidget(buffer)
        scroll_area.setWidgetResizable(True)
        layout = QHBoxLayout(buffer)
        base_layout = QHBoxLayout(self)
        buffer.setLayout(layout)
        base_layout.addWidget(scroll_area)
        self.setLayout(base_layout)
        self._base = buffer

        leftside = QWidget(self._base)
        leftlayout = QVBoxLayout(leftside)
        leftside.setLayout(leftlayout)

        layout.addWidget(leftside)

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
        if visualiser_side is not None:
            self._visualiser = visualiser_side
            leftlayout.addWidget(self._visualiser)

        self._leftlayout = leftlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout

    def connect_logging(self):
        self.error.connect(self._tab_reference.error)
        for thing in [self._visualiser]:
            thing.error.connect(self._tab_reference.error)

    @Slot(str)
    def set_label_text(self, text: str):
        self._tab_label.setTextFormat(Qt.TextFormat.RichText)
        self._tab_label.setWordWrap(True)
        self._tab_label.setText(text)

    def add_button(self, label: str = "Button!", slot=None, upper=True):
        temp = QPushButton(label, self._base)
        if slot is not None:
            temp.clicked.connect(slot)
        if upper:
            self._ub_layout.addWidget(temp)
        else:
            self._lb_layout.addWidget(temp)
