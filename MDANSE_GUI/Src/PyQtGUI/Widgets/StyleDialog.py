
from typing import Union, Iterable, Optional
from collections import OrderedDict
import copy

from icecream import ic
from qtpy.QtWidgets import QDialog, QPushButton, QFileDialog, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QComboBox, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout, QCheckBox, QTextEdit
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel,\
                        QObject
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel,\
                    QIntValidator, QDoubleValidator, QValidator

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE_GUI.PyQtGUI.Widgets.GeneralWidgets import InputFactory


sample_styles = {
'initial_stylesheet' : """QWidget
{   background-color:rgb(230,250,250);
    border-radius: 6px;
    border-style: outset;
    border-width: 4px;
    border-color: rgb(30,250,250);
    font: bold 14px;
    min-width: 10em;
    padding: 6px;
}""",


'dark_stylesheet' : """QWidget
{   background-color:rgb(80,10,80);
    border-radius: 6px;
    border-style: outset;
    border-width: 4px;
    border-color: rgb(10,20,200);
    font: bold 14px;
    color: rgb(10,200,10);
    min-width: 10em;
    padding: 6px;
}"""
}


class StyleDatabase(QObject):

    stored_style = Signal(str)
    stored_labels = Signal(list)

    def __init__(self, parent: Optional['QObject'] = ...) -> None:
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

    def __init__(self, *args, converter: IJob = 'Dummy', **kwargs):
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


        


        
