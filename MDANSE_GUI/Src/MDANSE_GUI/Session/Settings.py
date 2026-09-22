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

from pathlib import Path
from typing import Any

from more_itertools import first_true, only
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.Core.Settings import Settings, SettingsDict, SettingsRaw
from MDANSE_GUI.Utils import block_signals


class GUISettings(QStandardItemModel):
    def __init__(
        self,
        *args,
        settings: Path | SettingsRaw | None = None,
        save: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        Settings.init(settings, save=save)
        self.settings = Settings.settings

        self.populate_model()

        self.itemChanged.connect(self.on_value_changed)

    def __getitem__(self, key: tuple[str, str]) -> Any:
        return Settings.get_opt(*key)

    def __setitem__(self, key: tuple[str, str], value: Any) -> None:
        Settings.set_opt(*key, value)
        group = only(self.findItems(key[0]))

        if group is None:  # Need to regenerate
            self.populate_model()
            return

        item = first_true(
            (group.child(i) for i in range(group.rowCount())),
            pred=lambda x: x.data() == key[1],
        )

        if item is None:  # Need to regenerate
            self.populate_model()
            return

        valdata = group.child(item.row(), 1)

        assert valdata

        with block_signals(self):
            if isinstance(value, bool):
                valdata.setCheckState(
                    Qt.CheckState.Checked if value else Qt.CheckState.Unchecked
                )
                valdata.setData(value)
            else:
                valdata.setText(value)
                valdata.setData(value)

    def save(self, filename: Path | None = None) -> None:
        Settings.save(filename)

    def populate_model(self):
        self.clear()

        for section, settings in self.settings.items():
            section_item = QStandardItem(section)
            section_item.setData(section)
            section_item.setEditable(False)
            section_comment_item = QStandardItem("")

            self.appendRow([section_item, QStandardItem(), section_comment_item])

            for value in settings.values():
                key_item = QStandardItem(value.name)

                if isinstance(value.value, bool):
                    value_item = QStandardItem()
                    value_item.setCheckable(True)
                    value_item.setCheckState(
                        Qt.CheckState.Checked
                        if value.value
                        else Qt.CheckState.Unchecked
                    )
                    value_item.setData(value.value)
                else:
                    value_item = QStandardItem(value.value)
                    value_item.setData(value.value)

                key_item.setData(value.name)
                key_item.setEditable(False)

                comment_item = QStandardItem(value.comment)
                comment_item.setData(value.comment)

                comment_item.setEditable(False)
                section_item.appendRow([key_item, value_item, comment_item])

        for i, label in enumerate(("Item", "Value", "Comment")):
            self.setHeaderData(i, Qt.Orientation.Horizontal, label)

    @Slot("QStandardItem*")
    def on_value_changed(self, item: QStandardItem) -> None:
        index = item.index()
        row = index.row()

        if item.isCheckable():
            new_contents = item.checkState() is Qt.CheckState.Checked
        else:
            new_contents = index.data(role=Qt.ItemDataRole.DisplayRole)
        group_item = item.parent()

        if group_item is None:
            return

        item_key = group_item.child(row, 0).data(role=Qt.ItemDataRole.DisplayRole)
        group_key = group_item.data(role=Qt.ItemDataRole.DisplayRole)

        self[group_key, item_key] = new_contents
