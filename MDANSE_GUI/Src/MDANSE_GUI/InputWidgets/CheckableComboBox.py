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

from itertools import count, groupby

from qtpy.QtCore import QEvent, QObject, Qt
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
        self.item_text_castable_to_int = True
        # it's faster to access the items through this python list than
        # through self.model().item(idx)
        self.items = []
        # for a large number of items accessing the checked status and
        # text seems quite slow. We mirror the data in these lists for
        # improved performances.
        self.checked = []
        self.text = []
        self.select_all_item = None
        self.addItem("select all", underline=True)
        self.lineEdit().setText("")

    def clear(self):
        result = super().clear()
        self.items = []
        self.checked = []
        self.text = []
        self.select_all_item = None
        self.addItem("select all", underline=True)
        self.lineEdit().setText("")
        return result

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        """Updates the check state of the items and the lineEdit.

        Parameters
        ----------
        a0 : QObject or None
            A QT object.
        a1 : QEvent or None
            A QT event.
        """
        if a0 == self.view().viewport() and a1.type() == QEvent.MouseButtonRelease:
            idx = self.view().indexAt(a1.pos()).row()
            item = self.model().item(idx)

            if item.checkState() == Qt.Checked:
                set_checked = False
            else:
                set_checked = True

            if idx == 0:
                # need to block signals temporarily otherwise as we
                # need to make a change on all the items which could
                # cause alot of signals to be emitted
                self.model().blockSignals(True)
                for i in range(self.n_items):
                    self.set_item_checked_state(i, set_checked)
                self.model().blockSignals(False)
                self.select_all_item.setCheckState(
                    Qt.Checked if set_checked else Qt.Unchecked
                )
            else:
                self.set_item_checked_state(idx - 1, set_checked)
                self.update_all_selected()

            self.update_line_edit()
            return True

        return super().eventFilter(a0, a1)

    @property
    def n_items(self) -> int:
        """
        Returns
        -------
        int
            Number of items not including the select all item.
        """
        return len(self.items)

    def set_item_checked_state(self, idx: int, set_checked: bool):
        """Checks the item and updates the checked list.

        Parameters
        ----------
        idx : int
            Index of the item in the self.items list.
        set_checked : bool
            Checks the item if true.
        """
        if self.checked[idx] == set_checked:
            return

        if set_checked:
            check_uncheck = Qt.Checked
        else:
            check_uncheck = Qt.Unchecked

        self.checked[idx] = set_checked
        self.items[idx].setCheckState(check_uncheck)

    def update_all_selected(self):
        """check/uncheck select all since everything is/isn't selected."""
        if all(self.checked):
            self.select_all_item.setCheckState(Qt.Checked)
        else:
            self.select_all_item.setCheckState(Qt.Unchecked)

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

        if text == "select all":
            self.select_all_item = item
        else:
            self.items.append(item)
            self.checked.append(False)
            self.text.append(text)
            if self.item_text_castable_to_int:
                try:
                    int(text)
                except ValueError:
                    self.item_text_castable_to_int = False

    def update_line_edit(self) -> None:
        """Updates the lineEdit text of the combobox."""
        text = [i for i, j in zip(self.text, self.checked) if j]
        if self.item_text_castable_to_int:
            vals = [int(i) for i in text]
            # changes for example 1,2,3,5,6,7,9,10 -> 1-3,5-7,9-10
            gr = (list(x) for _, x in groupby(vals, lambda x, c=count(): next(c) - x))
            text = ",".join("-".join(map(str, (g[0], g[-1])[: len(g)])) for g in gr)
            self.lineEdit().setText(text)
        else:
            self.lineEdit().setText(",".join(text))

    def set_default(self, default: str) -> None:
        """Checks the item with the text equal to the default parameter.

        Parameters
        ----------
        default : str
            Parameter used to check items in the combobox.
        """
        for i in range(self.n_items):
            text = self.text[i]
            if text == default:
                self.set_item_checked_state(i, True)
            else:
                self.set_item_checked_state(i, False)
        self.update_line_edit()

    def checked_values(self) -> list[str]:
        """
        Returns
        -------
        list[str]
            List of items texts that are checked.
        """
        result = []
        for i in range(self.n_items):
            if self.checked[i]:
                result.append(self.text[i])
        return result
