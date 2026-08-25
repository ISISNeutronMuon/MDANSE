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

from collections.abc import Iterable
from functools import partial
from operator import is_
from typing import ClassVar, Literal

from more_itertools import first_true
from qtpy.QtCore import QModelIndex, QObject, Qt, Signal, Slot
from qtpy.QtGui import QBrush, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QSizePolicy,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import Never, override

from MDANSE.Framework.Configurators.ExtXYZColumnMapConfigurator import (
    ExtXYZColumnMapConfigurator,
)
from MDANSE.Framework.Converters import ExtXYZ
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.items: list[str] = []

    def setItems(self, items: Iterable[str]) -> None:
        self.items = list(items)

    @override
    def createEditor(
        self, parent: QWidget | None, option: QStyleOptionViewItem, index: QModelIndex
    ) -> QComboBox:
        editor = QComboBox(parent)
        editor.addItems(self.items)
        return editor

    @override
    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        value = index.model().data(index)
        if value:
            editor.setCurrentIndex(self.items.index(value))

    @override
    def setModelData(
        self, editor: QComboBox, model: QStandardItemModel, index: QModelIndex
    ) -> None:
        model.setData(index, editor.currentText())


class ColumnAssignModel(QStandardItemModel):
    KNOWN_PROPS: ClassVar[tuple[str, ...]] = (
        *ExtXYZColumnMapConfigurator.KEY_DEFAULTS.keys(),
        "None",
    )

    def __init__(self, *args, config: ExtXYZColumnMapConfigurator, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegate = ComboBoxDelegate()
        self.delegate.setItems(())
        self.config = config

    def update(self):
        self.config.configure()
        self.clear()
        self.delegate.setItems(self.config.columns)
        for name, comp in self.config.mapping.items():
            label = QStandardItem(name)
            label.setEditable(False)
            val = QStandardItem(comp)
            self.appendRow((label, val))

    @property
    def settings(self) -> dict[str, str | None]:
        conf = {
            self.item(row, 0).text(): elem if elem != "None" else None
            for row in range(self.rowCount())
            if (elem := self.item(row, 1).text())
        }
        self.config.configure(conf)
        return conf


class ExtXYZColumnWidget(WidgetBase):
    def __init__(
        self,
        *args,
        layout_type: Literal["QVBoxLayout"] = "QVBoxLayout",
        configurator: ExtXYZColumnMapConfigurator,
        **kwargs,
    ):
        super().__init__(
            *args, layout_type=layout_type, configurator=configurator, **kwargs
        )

        self._file_widget = first_true(
            self.parent()._widgets,
            pred=lambda x: (
                x._configurator
                is self._configurator.configurable[
                    self._configurator.dependencies["input_file"]
                ]
            ),
            default=None,
        )
        if not self._file_widget:
            raise ValueError("No input widget defined")

        self.model = ColumnAssignModel(config=self._configurator)

        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setItemDelegateForColumn(1, self.model.delegate)

        self._layout.addWidget(self.view)
        self._file_widget.value_changed.connect(self.update)

    def get_widget_value(self) -> dict[str, str | None]:
        return self.model.settings

    @Slot()
    def update(self) -> None:
        if self._file_widget._configurator.valid:
            self.model.update()
