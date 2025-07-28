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

from contextlib import suppress

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QItemDelegate,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionProgressBar,
)


class ColourPicker(QStyledItemDelegate):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        dialog = QColorDialog(parent)
        return dialog

    def setEditorData(self, editor, index):
        colour_string = index.data()
        color = QColor(colour_string)
        editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        if editor.result() == QColorDialog.DialogCode.Accepted:
            color = editor.currentColor()
            colour_string = color.toRgb()
            model.setData(index, colour_string)
            model.setData(index, color, role=Qt.ItemDataRole.BackgroundRole)


class MainAxisCombo(QItemDelegate):
    def __init__(self, *args, **kwargs) -> None:
        self._items = []
        super().__init__(*args, **kwargs)

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, Qt.DisplayRole)
        try:
            i = self._items.index(text)
        except ValueError:
            i = 0
        editor.setCurrentIndex(i)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        model = index.model()
        key = index.model().data(index, Qt.ItemDataRole.UserRole)
        dataset = model._datasets[key]
        self._items = [str(x) for x in dataset._axes.keys()]
        combo.addItems(self._items)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo

    @Slot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class MplStyleCombo(QItemDelegate):
    def __init__(self, *args, mpl_items=None, **kwargs) -> None:
        self._items = list([str(x) for x in mpl_items.keys()])
        super().__init__(*args, **kwargs)

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, Qt.DisplayRole)
        try:
            i = self._items.index(text)
        except ValueError:
            i = 0
        editor.setCurrentIndex(i)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        li = []
        for item in self._items:
            li.append(item)
        combo.addItems(li)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo

    @Slot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class RadiusSpinBox(QItemDelegate):
    def __init__(self, *args, mpl_items=None, **kwargs) -> None:
        self._minimum = 0.0
        self._step = 0.01
        super().__init__(*args, **kwargs)

    def setEditorData(self, editor, index):
        current_value = float(index.data())
        editor.setValue(current_value)

    def setModelData(self, editor, model, index):
        model.setData(index, str(round(editor.value(), 2)))

    def createEditor(self, parent, option, index):
        sbox = QDoubleSpinBox(parent)
        sbox.setMinimum(self._minimum)
        sbox.setSingleStep(self._step)
        sbox.valueChanged.connect(self.valueChanged)
        return sbox

    @Slot()
    def valueChanged(self):
        self.commitData.emit(self.sender())


class ProgressDelegate(QItemDelegate):
    progress_role = Qt.UserRole + 1000

    def paint(self, painter, option, index):
        progress = index.data(self.progress_role)
        progress_max = max(index.data(self.progress_role + 1), 1)
        rate = index.data(self.progress_role + 2)
        try:
            int(progress)
        except Exception:
            progress = 0
        opt = QStyleOptionProgressBar()
        opt.rect = option.rect
        opt.minimum = 0
        opt.maximum = progress_max
        opt.progress = progress
        opt.text = f"{progress / progress_max:.2%}"
        with suppress(Exception):
            opt.text += f" ({round(float(rate), 2)} %/s)"

        opt.textVisible = True
        QApplication.style().drawControl(QStyle.CE_ProgressBar, opt, painter)
