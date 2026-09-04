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
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
    from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel


class Panel(QWidget):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    error = Signal(str)
    item_picked = Signal(object)

    def __init__(
        self,
        *args,
        data_side: QWidget | None = None,
        visualiser_side: QWidget | None = None,
        tab_reference: GeneralTab | None = None,
        **kwargs,
    ):
        self._visualiser = visualiser_side
        self._tab_reference = tab_reference
        self._model = None
        self._view = data_side

        super().__init__(*args, **kwargs)

        self._base = QWidget(self)
        self._layout = QHBoxLayout(self._base)
        self._base.setLayout(self._layout)

        self._base_layout = QHBoxLayout(self)
        self.setLayout(self._base_layout)

        self._leftside = QWidget(self._base)
        self._leftlayout = QVBoxLayout(self._leftside)
        self._leftside.setLayout(self._leftlayout)

        self._tab_label = QLabel(self._leftside)
        self._leftlayout.addWidget(self._tab_label)

        upper_buttons = QWidget(self._leftside)
        self._ub_layout = QHBoxLayout(upper_buttons)
        upper_buttons.setLayout(self._ub_layout)
        self._leftlayout.addWidget(upper_buttons)

        lower_buttons = QWidget(self._leftside)
        self._lb_layout = QHBoxLayout(lower_buttons)
        lower_buttons.setLayout(self._lb_layout)
        self._leftlayout.addWidget(lower_buttons)

    @Slot(str)
    def set_label_text(self, text: str):
        self._tab_label.setTextFormat(Qt.TextFormat.RichText)
        self._tab_label.setWordWrap(True)
        self._tab_label.setText(text)

    def add_widget(self, tempwidget: QWidget | None = None, *, upper: bool = True):
        if upper:
            self._ub_layout.addWidget(tempwidget)
        else:
            self._lb_layout.addWidget(tempwidget)

    def set_model(self, model: GeneralModel):
        self._model = model
        self._view.setModel(model)

    def current_item(self):
        try:
            index = self._view.currentIndex()
            item = self._model.itemFromIndex(index)
        except Exception as e:
            self.error.emit(repr(e))
        else:
            return item

    def add_button(
        self,
        label: str = "Button!",
        slot: Callable | None = None,
        *,
        upper: bool = True,
    ):
        temp = QPushButton(label, self._base)
        if slot is not None:
            temp.clicked.connect(slot)
        self.add_widget(temp, upper=upper)
