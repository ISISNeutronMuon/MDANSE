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
from qtpy.QtCore import Qt, QEvent, Slot, QObject
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
)
from MDANSE.Framework.AtomSelector import Selector
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


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
        self.addItem("select all")
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
                # check/uncheck select all since everything is/isn't selected
                if all([i.checkState() == Qt.Checked for i in self.getItems()]):
                    self.model().item(0).setCheckState(Qt.Checked)
                else:
                    self.model().item(0).setCheckState(Qt.Unchecked)

            self.update_line_edit()
            return True

        return super().eventFilter(a0, a1)

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

    def addItem(self, text: str) -> None:
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


class HelperDialog(QDialog):
    """Generates a string that specifies the atom selection.

    Attributes
    ----------
    _cbox_text : dict
        The dictionary that maps the selector settings to text used in
        the helper dialog.
    """

    _cbox_text = {
        "all": "All atoms (excl. dummy atoms):",
        "dummy": "All dummy atoms:",
        "hs_on_heteroatom": "Hs on heteroatoms:",
        "primary_amine": "Primary amine groups:",
        "hydroxy": "Hydroxy groups:",
        "methyl": "Methyl groups:",
        "phosphate": "Phosphate groups:",
        "sulphate": "Sulphate groups:",
        "thiol": "Thiol groups:",
        "water": "Water molecules:",
        "element": "Elements:",
        "hs_on_element": "Hs on elements:",
        "index": "Indexes:",
        "invert": "Invert the selection:",
    }

    def __init__(self, selector: Selector, field: QLineEdit, parent, *args, **kwargs):
        """
        Parameters
        ----------
        selector : Selector
            The MDANSE selector initialized with the current chemical
            system.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Atom selection helper")
        self.min_width = kwargs.get("min_width", 450)
        self.resize(self.min_width, self.height())
        self.setMinimumWidth(self.min_width)
        self.selector = selector
        self._field = field
        self.full_settings = self.selector.full_settings
        match_exists = self.selector.match_exists

        self.left = QVBoxLayout()

        select = QGroupBox("selection")
        select_layout = QVBoxLayout()
        invert = QGroupBox("inversion")
        invert_layout = QVBoxLayout()

        self.check_boxes = []
        self.combo_boxes = []

        for k, v in self.full_settings.items():

            if isinstance(v, bool):
                check_layout = QHBoxLayout()
                checkbox = QCheckBox()
                checkbox.setChecked(v)
                checkbox.setLayoutDirection(Qt.RightToLeft)
                label = QLabel(self._cbox_text[k])
                checkbox.setObjectName(k)
                checkbox.stateChanged.connect(self.update)
                if not match_exists[k]:
                    checkbox.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.check_boxes.append(checkbox)
                check_layout.addWidget(label)
                check_layout.addWidget(checkbox)
                if k == "invert":
                    invert_layout.addLayout(check_layout)
                else:
                    select_layout.addLayout(check_layout)

            elif isinstance(v, dict):
                combo_layout = QHBoxLayout()
                combo = CheckableComboBox()
                items = [i for i in v.keys() if match_exists[k][i]]
                # we blocksignals here as there can be some
                # performance issues with a large number of items
                combo.model().blockSignals(True)
                combo.addItems(items)
                combo.model().blockSignals(False)
                combo.setObjectName(k)
                combo.model().dataChanged.connect(self.update)
                label = QLabel(self._cbox_text[k])
                if len(items) == 0:
                    combo.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.combo_boxes.append(combo)
                combo_layout.addWidget(label)
                combo_layout.addWidget(combo)
                select_layout.addLayout(combo_layout)

        select.setLayout(select_layout)
        invert.setLayout(invert_layout)
        self.left.addWidget(select)
        self.left.addWidget(invert)

        bottom = QHBoxLayout()
        apply = QPushButton("Apply")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        close.clicked.connect(self.close)
        bottom.addWidget(apply)
        bottom.addWidget(close)

        self.left.addLayout(bottom)
        self.right = QTextEdit()
        self.right.setReadOnly(True)

        layout = QHBoxLayout()
        layout.addLayout(self.left, 5)
        layout.addWidget(self.right, 4)

        self.setLayout(layout)
        self.update()

    def update(self) -> None:
        """Using the checkbox and combobox widgets: update the settings,
        get the selection and update the textedit box with details of
        the current selection.
        """
        for check_box in self.check_boxes:
            self.full_settings[check_box.objectName()] = check_box.isChecked()
        for combo_box in self.combo_boxes:
            for item in combo_box.getItems():
                self.full_settings[combo_box.objectName()][item.text()] = (
                    item.checkState() == Qt.Checked
                )

        self.selector.update_settings(self.full_settings)
        idxs = self.selector.get_idxs()
        num_sel = len(idxs)

        text = [f"Number of atoms selected:\n{num_sel}\n\nSelected atoms:\n"]
        atoms = self.selector.system.atom_list
        for idx in idxs:
            text.append(f"{idx})  {atoms[idx].full_name}\n")

        self.right.setText("".join(text))

    def apply(self) -> None:
        """Set the field of the AtomSelectionWidget to the currently
        chosen setting in this widget.
        """
        self.selector.update_settings(self.full_settings)
        self._field.setText(self.selector.settings_to_json())


class AtomSelectionWidget(WidgetBase):
    """The atoms selection widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = '{"all": true}'
        self._value = default_value
        self._field = QLineEdit(default_value, self._base)
        self._field.setPlaceholderText(default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        self._field.textChanged.connect(self.updateValue)
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Specify which atoms will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."
        self.selector = self._configurator.get_selector()
        self.helper = HelperDialog(self.selector, self._field, self._base)
        helper_button = QPushButton("Atom selection helper", self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._default_value = default_value
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(tooltip_text)

    @Slot()
    def helper_dialog(self) -> None:
        """Opens the helper dialog."""
        if self.helper.isVisible():
            self.helper.close()
        else:
            self.helper.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.
        """
        selection_string = self._field.text()
        if len(selection_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return selection_string
