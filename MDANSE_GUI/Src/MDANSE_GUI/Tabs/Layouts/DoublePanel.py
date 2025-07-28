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
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel


class DoublePanel(QWidget):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    error = Signal(str)
    item_picked = Signal(object)

    def __init__(
        self,
        *args,
        data_side=None,
        visualiser_side=None,
        tab_reference=None,
        **kwargs,
    ):
        self._model = None
        self._view = None
        self._visualiser = None

        self._tab_reference = tab_reference

        super().__init__(*args, **kwargs)

        buffer = QWidget(self)
        layout = QHBoxLayout(buffer)
        base_layout = QHBoxLayout(self)
        buffer.setLayout(layout)
        self.setLayout(base_layout)
        self._base = buffer
        self._splitter = QSplitter(self._base)
        base_layout.addWidget(self._splitter)

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
        if data_side is not None:
            leftlayout.addWidget(data_side)
            self._view = data_side
        leftlayout.addWidget(lower_buttons)

        self._leftlayout = leftlayout
        self._rightlayout = rightlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout

        if visualiser_side is not None:
            self._visualiser = visualiser_side
            self._rightlayout.addWidget(visualiser_side)
            if self._view is not None:
                self._view.connect_to_visualiser(visualiser_side)

        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 2)

    def connect_logging(self):
        self.error.connect(self._tab_reference.error)
        for thing in [self._view, self._visualiser, self._model]:
            thing.error.connect(self._tab_reference.error)

    def set_model(self, model: GeneralModel):
        self._model = model
        self._view.setModel(model)

    @Slot(str)
    def set_label_text(self, text: str):
        self._tab_label.setTextFormat(Qt.TextFormat.RichText)
        self._tab_label.setWordWrap(True)
        self._tab_label.setText(text)

    def add_widget(self, tempwidget: QWidget = None, upper=True):
        if upper:
            self._ub_layout.addWidget(tempwidget)
        else:
            self._lb_layout.addWidget(tempwidget)

    def add_button(self, label: str = "Button!", slot=None, upper=True):
        temp = QPushButton(label, self._base)
        if slot is not None:
            temp.clicked.connect(slot)
        if upper:
            self._ub_layout.addWidget(temp)
        else:
            self._lb_layout.addWidget(temp)

    def current_item(self):
        try:
            index = self._view.currentIndex()
            item = self._model.itemFromIndex(index)
        except Exception as e:
            self.error.emit(repr(e))
        else:
            return item
