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

import os
from pathlib import PurePath

import tomlkit
from qtpy.QtCore import QModelIndex, QObject, Qt, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG


class UserSettingsModel(QStandardItemModel):
    file_loaded = Signal(str)

    def __init__(self, *args, settings_filename: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        if settings_filename:
            self._settings = SettingsFile(settings_filename)
            self._settings.load_from_file()
        else:
            LOG.warning("Called UserSettingsModel without settings_filename")
            return
        self._entries_present = {}
        self._groups_present = {}
        self.populate_model()
        self.setHeaderData(0, Qt.Orientation.Horizontal, "Item")
        self.setHeaderData(1, Qt.Orientation.Horizontal, "Value")
        self.setHeaderData(2, Qt.Orientation.Horizontal, "Comment")

        self.dataChanged.connect(self.save_new_value)
        # self.scan_model()

    def refresh(self):
        # self._settings.load_from_file()
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
        for number, groupname in enumerate(self._settings.keys()):
            group = self._settings.group(groupname)
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
                    self._entries_present[(section, key)] = [
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
        if column_number == 1:
            if not group.set(item_name, new_value):
                LOG.warning(
                    f"Modify item: could not set item {item_name} to value {new_value} in group {group_name}"
                )
                LOG.debug(group.as_toml())
        elif column_number == 2:
            if not group.set_comment(item_name, new_value):
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
        obsolete_values, obsolete_comments = [], []
        for key in self._settings:
            if key not in settings:
                obsolete_values.append(key)
        for key in self._comments:
            if key not in comments:
                obsolete_comments.append(key)
        return obsolete_values, obsolete_comments

    def as_toml(self):
        results = tomlkit.table()
        results.comment(self._group_comment)
        for key in self._settings.keys():
            results[key] = self._settings[key]
            results[key].comment(self._comments.get(key, "---"))
        return results

    def as_dict(self):
        return self._settings


class SettingsFile:
    def __init__(self, name, settings_path: str = None):
        if settings_path is None:
            settings_path = PLATFORM.application_directory()
        self._top_name = name
        self._filename = os.path.join(settings_path, name + ".toml")
        self._tomldoc = None
        self._file = TOMLFile(self._filename)
        self._groups = {}
        self._defaults = {}
        self.load_from_file()

    def load_from_file(self) -> bool:
        file = TOMLFile(self._filename)
        try:
            self._tomldoc = file.read()
        except FileNotFoundError:
            LOG.warning(f"File {self._filename} does not exists.")
            return False
        except ParseError:
            LOG.warning(f"File {self._filename} could not be parsed.")
            return False
        else:
            for key in self._tomldoc.keys():
                table = self._tomldoc[key]
                group = self._groups.get(key, SettingsGroup(key))
                temp_values, temp_comments = {}, {}
                for inner_key in table.keys():
                    temp_values[inner_key] = table[inner_key]
                    temp_comments[inner_key] = table[inner_key].trivia.comment
                group.populate(temp_values, temp_comments)
                self._groups[key] = group
            return True

    def keys(self):
        return self._groups.keys()

    @property
    def groups(self):
        return self._groups

    def default_value(self, group: str, key: str):
        try:
            result = self._defaults[(group, key)]
        except KeyError:
            result = None
        LOG.warning(
            f"Bad entry in {self._filename} for {group}->{key}? Default value {result} requested."
        )
        return result

    def group(self, group_name: str) -> SettingsGroup:
        try:
            group = self._groups[group_name]
        except KeyError:
            group = SettingsGroup(group_name)
            self._groups[group_name] = group
        return group

    def save_values(self):
        newdoc = tomlkit.document()
        for gr in self._groups.values():
            newdoc[gr._name] = gr.as_toml()
        file = TOMLFile(self._filename)
        file.write(newdoc)

    def overwrite_settings(self, group_name, values, comments):
        group = self.group(group_name)
        group.populate(values, comments)

    def extend_settings(self, group_name, values, comments):
        group = self.group(group_name)
        group.update(values, comments)
        for key, value in values.items():
            self._defaults[(group_name, key)] = value

    def check_settings(self, group_name, values, comments):
        group = self.group(group_name)
        unused_values, unused_comments = group.compare(values, comments)
        for val in unused_values:
            LOG.warning(
                f"Unnecessary entry {val} in file {self._filename}, group {group._name}"
            )


class StructuredSession(QObject):
    """Stores settings of different parts of the GUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._models = {}
        self._configs = {}
        self._reserved_filenames = []
        self._state = None
        self._main_config_name = "mdanse_general_settings"
        self._filename = kwargs.get("filename", self._main_config_name)
        self.populate_defaults()

    def connect_settings_file(self, name: str):
        model = UserSettingsModel(settings_filename=name)
        sf = model._settings
        self._configs[name] = sf
        self._models[name] = model
        return sf

    @Slot()
    def save(self):
        for _, config in self._configs.items():
            config.save_values()

    def load(self, fname: str = None):
        """Included for compatibility with LocalSession only.
        Now each component loads its own config separately."""

    def reserved_filenames(self) -> list[str]:
        return self._reserved_filenames

    @Slot(str)
    def protect_filename(self, some_filename: str):
        new_filename = PurePath(os.path.abspath(some_filename))
        self._reserved_filenames.append(new_filename)

    @Slot(str)
    def free_filename(self, some_filename: str):
        filename = PurePath(os.path.abspath(some_filename))
        if filename in self._reserved_filenames:
            index = self._reserved_filenames.index(filename)
            self._reserved_filenames.pop(index)

    def main_settings(self):
        return self._configs[self._main_config_name]

    def obtain_settings(self, gui_element):
        try:
            name = gui_element._name
        except AttributeError:
            name = self._main_config_name
        try:
            sf = self._configs[name]
        except KeyError:
            sf = self.connect_settings_file(name)
        sf.load_from_file()

        try:
            setting_groups = gui_element.grouped_settings()
        except AttributeError:
            LOG.debug(
                f"GUI element {gui_element} did not have a grouped_settings method."
            )
        else:
            for gname, (settings, comments) in setting_groups.items():
                LOG.debug(f"Initialising values in {gname}")
                sf.extend_settings(gname, settings, comments)
                sf.check_settings(gname, settings, comments)
            sf.save_values()
        return sf

    def settings_model(self, settings_filename: str = ""):
        if settings_filename not in self._models:
            LOG.debug(f"session connecting to {settings_filename} for the first time")
            self.connect_settings_file(settings_filename)
        model = self._models[settings_filename]
        LOG.debug(f"session re-using the model {settings_filename}")
        self._configs[settings_filename].load_from_file()
        model.refresh()
        return model

    def populate_defaults(self):
        gs = self.connect_settings_file(self._main_config_name)
        gs.load_from_file()
        paths = gs.group("paths")
        paths.set_group_comment("Lookup of working directory paths for the main GUI")
        units = gs.group("units")
        units.set_group_comment(
            "The GUI will, where possible and indicated, use these physical units."
        )
        paths.add(
            "root_directory",
            os.path.expanduser("~"),
            "Starting path for any file search",
        )
        units.add("energy", "meV", "The unit of energy preferred by the user.")
        units.add("time", "fs", "The unit of time preferred by the user.")
        units.add("distance", "ang", "The unit of distance preferred by the user")
        units.add(
            "reciprocal", "1/ang", "The momentum (transfer) unit preferred by the user"
        )
        gs.save_values()
        self._configs[self._main_config_name] = gs

    def get_path(self, key: str) -> str:
        settings = self._configs[self._main_config_name]
        group = settings["paths"]
        value = group.get(key, os.path.abspath("."))
        return value

    def set_path(self, key: str, value: str):
        settings = self._configs[self._main_config_name]
        group = settings["paths"]
        group.set(key, value)

    def get_unit(self, key: str) -> str:
        settings = self._configs[self._main_config_name]
        group = settings["units"]
        value = group.get(key, "N/A")
        return value
