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

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import tomlkit
from qtpy.QtCore import QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from collections.abc import Iterable

T = TypeVar("T")
DEFAULT_SETTINGS_PATH = PLATFORM.application_directory()


class Settings(Generic[T], QStandardItemModel):
    def __init__(self, *args, settings: T | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        if settings is not None:
            self.load_settings(settings)
        else:
            self._settings = {}

        self._entries_present = {}
        self._groups_present = {}
        self.populate_model()
        self.setHeaderData(0, Qt.Orientation.Horizontal, "Item")
        self.setHeaderData(1, Qt.Orientation.Horizontal, "Value")
        self.setHeaderData(2, Qt.Orientation.Horizontal, "Comment")

        self.dataChanged.connect(self.save_new_value)
        # self.scan_model()

    @abstractmethod
    def load_settings(self, settings: T) -> None: ...

    def refresh(self):
        self.populate_model()

    @Slot()
    def append_group(self):
        self.appendRow(
            [
                QStandardItem("new group, please rename"),
                QStandardItem(),
                QStandardItem("# new section"),
            ]
        )

    @Slot(int)
    def append_child(self, parent_row_number: int):
        parent_item = self.item(parent_row_number, 0)
        parent_item.appendRow(
            [
                QStandardItem("item"),
                QStandardItem("dummy_value"),
                QStandardItem("# new item!"),
            ]
        )

    def populate_model(self):
        for group in self._settings.values():
            section = group._name
            section_item = QStandardItem(section)
            section_item.setData(section)
            section_item.setEditable(False)
            section_comment = group._group_comment
            section_comment_item = QStandardItem(section_comment)

            if section not in self._groups_present:
                self.appendRow([section_item, QStandardItem(), section_comment_item])
                self._groups_present[section] = section_comment_item.index()

            for key, value in group.as_dict().items():
                key_item, value_item = QStandardItem(key), QStandardItem(value)
                key_item.setData(key)
                value_item.setData(value)
                comment = group._comments[key]
                comment_item = QStandardItem(comment)
                comment_item.setData(comment)
                key_item.setEditable(False)
                if (section, key) not in self._entries_present:
                    section_item.appendRow([key_item, value_item, comment_item])
                    self._entries_present[section, key] = [
                        value_item.index(),
                        comment_item.index(),
                    ]

    def scan_model(self):
        """This is meant to be used for debugging purposes only"""

        def scan_children(parent_item: QStandardItem):
            for row in range(parent_item.rowCount()):
                for column in range(parent_item.columnCount()):
                    item = parent_item.child(row, column)
                    LOG.debug(f"row={row}, column={column}, data={item.data()}")
                    if item.hasChildren():
                        scan_children(item)

        scan_children(self.invisibleRootItem())

    @Slot(QModelIndex)
    def save_new_value(self, item_index: QModelIndex):
        item = self.itemFromIndex(item_index)
        item_key = None
        row_number = item.row()
        column_number = item.column()
        new_value = item.data(role=Qt.ItemDataRole.DisplayRole)
        if item.parent() is not None:
            item_key = item.parent().child(row_number, 0).data()
            group_key = item.parent().data()
        else:
            group_key = new_value
        try:
            group = self._settings.group(group_key)
            if item_key is not None:
                if column_number == 1:
                    group.set(item_key, new_value)
                elif column_number == 2:
                    group.set_comment(item_key, new_value)
        except Exception:
            LOG.warning(
                f"Could not store {new_value} in group[{group_key}]->[{item_key}]"
            )
            LOG.debug(group.as_toml())

    def modify_group(self, group_name: str, new_value: str, column_number: int):
        if column_number == 2:
            group = self._settings.group(group_name)
            group.set_group_comment(new_value)

    def modify_item(
        self, group_name: str, item_name: str, new_value: str, column_number: int
    ):
        group = self._settings.group(group_name)
        group._group_comment = new_value
        if column_number == 1 and not group.set(item_name, new_value):
            LOG.warning(
                f"Modify item: could not set item {item_name} to value {new_value} in group {group_name}"
            )
            LOG.debug(group.as_toml())
        elif column_number == 2 and not group.set_comment(item_name, new_value):
            LOG.warning(
                f"Modify item: could not set comment {item_name} to value {new_value} in group {group_name}"
            )
            LOG.debug(group.as_toml())

    @Slot("QStandardItem*")
    def on_value_changed(self, item: QStandardItem):
        item_key = item.text()
        index = item.index()
        column = index.column()
        row = index.row()
        if column < 1 or column > 2:
            return
        new_contents = index.data(role=Qt.ItemDataRole.DisplayRole)
        group_item = item.parent()
        if group_item is None:
            self.modify_group(item_key, new_contents, column)
        else:
            item_key = group_item.child(row, 0).data(role=Qt.ItemDataRole.DisplayRole)
            group_key = group_item.data(role=Qt.ItemDataRole.DisplayRole)
            self.modify_item(group_key, item_key, new_contents, column)

    @Slot()
    def writeout_settings(self):
        self._settings.save_values()


class LocalSettings(Settings[dict[str, Any]]):
    def load_settings(self, settings: Path | str | dict[str, Any]) -> None:
        if isinstance(settings, (Path, str)):
            self._settings = SettingsDict(str(settings))
            path = Path(settings)

            if path.exists():
                self._settings.load_from_file(path)
        elif isinstance(settings, dict):
            self._settings = SettingsDict(settings.get("name", "dict"))
            self._settings.load_from_dict(settings)
        else:
            self._settings = {}


class UserSettingsModel(Settings[Path | str]):
    file_loaded = Signal(str)

    def load_settings(self, settings_filename: Path | str) -> None:
        self._settings = SettingsFile(settings_filename)
        self._settings.load_from_file()


class SettingsGroup:
    def __init__(self, group_name: str) -> None:
        self._name = group_name
        self._settings = {}
        self._comments = {}
        self._group_comment = ""

    def set_group_comment(self, comment: str):
        self._group_comment = comment

    def add(self, varname: str, value: str, comment: str):
        if varname not in self._settings:
            self._settings[varname] = value
            self._comments[varname] = comment

    def set(self, varname: str, value: str):
        if varname not in self._settings:
            LOG.warning(
                f"Group {self._name} has no entry {varname}. Add it first using add()."
            )
            return False
        self._settings[varname] = value
        return True

    def set_comment(self, varname: str, value: str):
        if varname not in self._settings:
            LOG.warning(
                f"Group {self._name} has no entry {varname}. Add it first using add()."
            )
            return False
        self._comments[varname] = value
        return True

    def get(self, varname: str):
        return self._settings[varname]

    def get_comment(self, varname: str):
        return self._comments[varname]

    def populate(self, settings: dict, comments: dict):
        for key, value in settings.items():
            self._settings[key] = value
            self._comments[key] = comments.get(key, "---")

    def update(self, settings: dict, comments: dict):
        for key, value in settings.items():
            if key in self._settings:
                continue
            self._settings[key] = value
            self._comments[key] = comments.get(key, "---")

    def compare(self, settings: dict, comments: dict):
        obsolete_values = self._settings.keys() - settings.keys()
        obsolete_comments = self._comments.keys() - comments.keys()
        return obsolete_values, obsolete_comments

    def as_toml(self):
        results = tomlkit.table()
        results.comment(self._group_comment)
        for key in self._settings:
            results[key] = self._settings[key]
            results[key].comment(self._comments.get(key, "---"))
        return results

    def as_dict(self):
        return self._settings


class SettingsContainer:
    def __init__(self, name: str):
        self._top_name = name
        self._groups = {}
        self._defaults = {}

    def group(self, group_name: str) -> SettingsGroup:
        return self._groups.setdefault(group_name, SettingsGroup(group_name))

    @property
    def groups(self) -> dict[str, SettingsGroup]:
        return self._groups

    def keys(self):
        return self.groups.keys()

    def items(self):
        return self.groups.items()

    def values(self):
        return self.groups.values()

    def __iter__(self):
        return iter(self.groups)

    def load_settings(self, filename: dict | Path | str | None = None) -> bool:
        if isinstance(filename, dict):
            self.load_from_dict(filename)
        elif not filename or isinstance(filename, (Path, str)):
            self.load_from_file(filename)

    def load_from_file(self, filename: Path | str | None = None) -> bool:
        filename = filename if filename is not None else self._filename

        try:
            tomldoc = TOMLFile(filename).read()
        except FileNotFoundError:
            LOG.warning(f"File {self._filename} does not exist.")
            return False
        except ParseError:
            LOG.warning(f"File {self._filename} could not be parsed.")
            return False

        for key, table in tomldoc.items():
            group = self.group(key)
            temp_values, temp_comments = {}, {}
            for inner_key in table:
                temp_values[inner_key] = table[inner_key]
                temp_comments[inner_key] = table[inner_key].trivia.comment
            group.populate(temp_values, temp_comments)
        return True

    def load_from_dict(self, settings: dict[str, dict[str, Any]]):
        for key, table in settings.items():
            group = self.group(key)
            group.populate(table, {})

    def save_values(self, filename: Path | str | None = None) -> None:
        newdoc = tomlkit.document()
        for gr in self._groups.values():
            newdoc[gr._name] = gr.as_toml()

        out_file = self._filename if filename is None else filename
        file = TOMLFile(out_file)
        file.write(newdoc)

    def overwrite_settings(
        self, group_name: str, values: Iterable[Any], comments: Iterable[str]
    ):
        group = self.group(group_name)
        group.populate(values, comments)

    def extend_settings(
        self, group_name: str, values: Iterable[Any], comments: Iterable[str]
    ):
        group = self.group(group_name)
        group.update(values, comments)
        for key, value in values.items():
            self._defaults[group_name, key] = value

    def check_settings(
        self, group_name: str, values: Iterable[Any], comments: Iterable[str]
    ):
        group = self.group(group_name)
        unused_values, _unused_comments = group.compare(values, comments)
        for val in unused_values:
            LOG.warning(
                f"Unnecessary entry {val} in file {self._filename}, group {group._name}"
            )


class SettingsDict(SettingsContainer):
    def save_values(self, filename: Path | str | None = None):
        if filename is not None:
            super().save_values(filename)

    def load_settings(self, filename: dict | Path | str | None = None) -> bool:
        if isinstance(filename, dict):
            self.load_from_dict(filename)
        elif isinstance(filename, (Path, str)):
            self.load_from_file(filename)

    def load_from_file(self, filename: Path | str):
        super().load_from_file(filename)

    def default_value(self, group: str, key: str):
        result = self._defaults.get((group, key))
        if result is None:
            LOG.warning(
                f"Missing entry in {type(self).__name__} for {group}->{key}? Default value {result} requested."
            )

        return result


class SettingsFile(SettingsContainer):
    def __init__(self, name: str, settings_path: Path | str = DEFAULT_SETTINGS_PATH):
        super().__init__(name)
        self._filename = (Path(settings_path) / name).with_suffix(".toml")

    def default_value(self, group: str, key: str):
        result = self._defaults.get((group, key))
        if result is None:
            LOG.warning(
                f"Bad entry in {self._filename} for {group}->{key}? Default value {result} requested."
            )

        return result
