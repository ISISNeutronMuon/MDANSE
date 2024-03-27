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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Research Software Group at ISIS (see AUTHORS)

from typing import Union, Iterable, Optional
from collections import OrderedDict
import copy

from icecream import ic
from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QFileDialog,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QApplication,
    QComboBox,
    QMenu,
    QLineEdit,
    QTableView,
    QFormLayout,
    QHBoxLayout,
    QCheckBox,
    QTextEdit,
)
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel, QObject
from qtpy.QtGui import (
    QFont,
    QEnterEvent,
    QStandardItem,
    QStandardItemModel,
    QIntValidator,
    QDoubleValidator,
    QValidator,
)

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE_GUI.Widgets.GeneralWidgets import InputFactory


sample_styles = {
    "blank_stylesheet": "",
    "initial_stylesheet": """QWidget
{   border-radius: 1px;
    border-style: 1nset;
    border-width: 0px;
    border-color: rgb(30,250,250);
    font: bold 14px;
    padding: 2px;
}""",
    "dark_stylesheet": """QWidget
{   background-color:rgb(40,10,80);
    border-radius: 6px;
    border-style: outset;
    border-width: 2px;
    border-color: rgb(10,20,200);
    font: bold 14px;
    color: rgb(10,200,10);
    padding: 3px;
}""",
    "hippie_stylesheet": """QWidget
{   background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop: 0 #aa1163, stop: 1 #23bb54);
    border-radius: 10px;
    border-style: outset;
    border-width: 3px;
    border-color: rgb(10,200,50);
    font: bold 14px;
    color: rgb(10,200,230);
    padding: 3px;
}""",
}


class StyleDatabase(QObject):
    stored_style = Signal(str)
    stored_labels = Signal(list)

    def __init__(self, parent: Optional["QObject"] = ...) -> None:
        super().__init__(parent)
        self._styles = sample_styles

    @Slot(list)
    def addStyleString(self, style: list[str]):
        label = style[0]
        text = style[1]
        self._styles[label] = text

    @Slot(str)
    def returnStyleString(self, label: str) -> str:
        try:
            temp = self._styles[label]
        except KeyError:
            return None
        else:
            self.stored_style.emit(temp)
            return temp

    @Slot()
    def showStoredLabels(self) -> list[str]:
        temp = [str(x) for x in self._styles.keys()]
        self.stored_labels.emit(temp)
        return temp


class StyleDialog(QDialog):
    new_style = Signal(str)
    icon_swap = Signal(bool)

    def __init__(self, *args, converter: IJob = "Dummy", **kwargs):
        super().__init__(*args, **kwargs)

        self._database = None

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self._selector = QComboBox(self)
        self._display = QTextEdit(self)
        self._confirm = QPushButton("Apply", self)
        self._confirm.clicked.connect(self.commitChanges)

        for x in [self._selector, self._display, self._confirm]:
            layout.addWidget(x)

    def connectStyleDatabase(self, dbase: StyleDatabase):
        self._database = dbase
        labels = dbase.showStoredLabels()
        self._selector.clear()
        [self._selector.addItem(lab) for lab in labels]
        dbase.stored_style.connect(self._display.setText)
        self._selector.currentTextChanged.connect(dbase.returnStyleString)
        self._selector.setCurrentIndex(0)

    def commitChanges(self):
        text = self._display.document().toPlainText()
        self.new_style.emit(text)
        label = self._selector.currentText()
        if "dark" in label:
            self.icon_swap.emit(True)
        else:
            self.icon_swap.emit(False)
