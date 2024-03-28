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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now


import glob
import itertools
import os
import os.path

from qtpy.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import AtomSelectionWidget


class AtomTransmutationWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        newline_button = QPushButton("Add transmutation", self._base)
        self._layout.addWidget(newline_button)
        self._lines = []
        self.updateValue()

    def add_line(self):
        line_base = QWidget(self._base)
        line_layout = QHBoxLayout(line_base)
        line_base.setLayout(line_layout)
        default_value = "all"
        starter = QLabel("Transmute ", line_base)
        leftfield = QLineEdit(default_value, self._base)
        spacer = QLabel(" to ", line_base)
        rightfield = QLineEdit("Au", self._base)
        for wid in [starter, leftfield, spacer, rightfield]:
            line_layout.append(wid)
        self._lines.append({"from": leftfield, "to": rightfield})

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def get_widget_value(self):
        result = []
        for line in self._lines:
            result.append((line["from"], line["to"]))
        if len(result) == 0:
            self._empty = True
            return None
        self._empty = False
        return result
