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
from typing import Union, Iterator
from itertools import count, groupby
from qtpy.QtCore import Qt, QEvent, QObject
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import QComboBox


class CheckableComboBox(QComboBox):
    """A multi-select checkable combobox"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.view().viewport().installEventFilter(self)
        self.view().setAutoScroll(False)
        # it's faster to access the items through this python list than
        # through self.model().item(idx)
        self._items = []
        self.addItem("select all", underline=True)
        self.lineEdit().setText("")

    def eventFilter(self, a0: Union[QObject, None], a1: Union[QEvent, None]) -> bool:
        """Updates the check state of the items and the lineEdit.

        Parameters
        ----------
        a0 : QObject or None
            A QT object.
        a1 : QEvent or None
            A QT event.
        """
        if a0 == self.view().viewport() and a1.type() == QEvent.MouseButtonRelease:
            idx = self.view().indexAt(a1.pos())
            item = self.model().item(idx.row())

            if item.checkState() == Qt.Checked:
                check_uncheck = Qt.Unchecked
            else:
                check_uncheck = Qt.Checked

            if idx.row() == 0:
                # need to block signals temporarily otherwise as we
                # need to make a change on all the items which could
                # cause alot of signals to be emitted
                self.model().blockSignals(True)
                for i in self.getItems():
                    i.setCheckState(check_uncheck)
                self.model().blockSignals(False)
                item.setCheckState(check_uncheck)
            else:
                item.setCheckState(check_uncheck)
                self.update_all_selected()

            self.update_line_edit()
            return True

        return super().eventFilter(a0, a1)

    def update_all_selected(self):
        """check/uncheck select all since everything is/isn't selected."""
        if all([i.checkState() == Qt.Checked for i in self.getItems()]):
            self.model().item(0).setCheckState(Qt.Checked)
        else:
            self.model().item(0).setCheckState(Qt.Unchecked)

    def addItems(self, texts: list[str]) -> None:
        """
        Parameters
        ----------
        texts : list[str]
            A list of items texts to add.
        """
        for text in texts:
            self.addItem(text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def addItem(self, text: str, bold=False, italic=False, underline=False) -> None:
        """
        Parameters
        ----------
        text : str
            The text of the item to add.
        """
        item = QStandardItem()
        item.setText(text)
        item.setEnabled(True)
        item.setCheckable(True)
        if bold or italic or underline:
            font = item.font()
            if bold:
                font.setBold(bold)
            if italic:
                font.setItalic(italic)
            if underline:
                font.setUnderline(underline)
            item.setFont(font)
        self.model().appendRow(item)
        self._items.append(item)

    def getItems(self) -> Iterator[QStandardItem]:
        """
        Yields
        ------
        QStandardItem
            Yields the items in the combobox except for the zeroth
            item because that is the select all item.
        """
        for i in range(self.model().rowCount()):
            if i == 0:  # skips the select all item
                continue
            yield self._items[i]

    def check_items_castable_to_int(self) -> bool:
        """
        Returns
        -------
        bool
            Returns true if the text of all items can be cast to int.
        """
        try:
            [int(i.text()) for i in self.getItems()]
            return True
        except ValueError:
            return False

    def update_line_edit(self) -> None:
        """Updates the lineEdit text of the combobox."""
        vals = []
        for item in self.getItems():
            if item.checkState() == Qt.Checked:
                vals.append(item.text())
        if self.check_items_castable_to_int():
            vals = [int(i) for i in vals]
            # changes for example 1,2,3,5,6,7,9,10 -> 1-3,5-7,9-10
            gr = (list(x) for _, x in groupby(vals, lambda x, c=count(): next(c) - x))
            text = ",".join("-".join(map(str, (g[0], g[-1])[: len(g)])) for g in gr)
            self.lineEdit().setText(text)
        else:
            self.lineEdit().setText(",".join(vals))

    def set_default(self, default: str) -> None:
        """Checks the item with the text equal to the default parameter.

        Parameters
        ----------
        default : str
            Parameter used to check items in the combobox.
        """
        model = self.model()
        for row_number in range(model.rowCount()):
            index = model.index(row_number, 0)
            item = model.itemFromIndex(index)
            text = model.data(index)
            if text == default:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        self.update_line_edit()

    def checked_values(self) -> list[str]:
        """
        Returns
        -------
        list[str]
            List of items texts that are checked.
        """
        result = []
        model = self.model()
        for row_number in range(model.rowCount()):
            if row_number == 0:
                continue
            index = model.index(row_number, 0)
            item = model.itemFromIndex(index)
            if item.checkState() == Qt.Checked:
                text = model.data(index)
                result.append(text)
        return result
