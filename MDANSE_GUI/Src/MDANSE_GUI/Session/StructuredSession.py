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

import os
from typing import Dict

from qtpy.QtCore import QObject, Signal, Slot

from MDANSE import PLATFORM
import tomlkit
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile


class SettingsGroup:

    def __init__(self, group_name: str) -> None:
        self._name = group_name
        self._settings = {}
        self._comments = {}

    def populate(self, settings: Dict, comments: Dict):
        for key, value in settings.items():
            self._settings[key] = value
            self._comments[key].comment(comments.get(key, "---"))

    def update(self, settings: Dict, comments: Dict):
        for key, value in settings.items():
            if key in self._settings:
                continue
            self._settings[key] = value
            self._comments[key].comment(comments.get(key, "---"))

    def compare(self, settings: Dict, comments: Dict):
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
        for key in self._settings.keys():
            results[key] = self._settings[key]
            results[key].comment(self._comments.get(key, "---"))
        return results


class SettingsFile:

    def __init__(self, name, settings_path: str = None):

        if settings_path is None:
            settings_path = PLATFORM.application_directory()
        self._top_name = name
        self._filename = os.path.join(settings_path, name + ".toml")
        self._file = TOMLFile(self._filename)
        self._groups = {}
        self.load_from_file()

    def load_from_file(self):
        try:
            tomldoc = self._file.read()
        except FileNotFoundError:
            print(f"File {self._filename} does not exists.")
        except ParseError:
            print(f"File {self._filename} could not be parsed.")
        else:
            for key in tomldoc.keys():
                table = tomldoc[key]
                group = self._groups.get(key, SettingsGroup(key))
                temp_values, temp_comments = {}, {}
                for inner_key in table.keys():
                    temp_values[inner_key] = table[inner_key]
                    temp_comments[inner_key] = table[inner_key].trivia.comment
                group.populate(temp_values, temp_comments)

    def save_values(self):
        newdoc = tomlkit.document()
        for gr in self._groups:
            newdoc[gr._name] = gr.as_toml()
        self._file.write(newdoc)

    def overwrite_settings(self, group_name, values, comments):
        group = self._groups.get(group_name, SettingsGroup(group_name))
        group.populate(values, comments)

    def extend_settings(self, group_name, values, comments):
        group = self._groups.get(group_name, SettingsGroup(group_name))
        group.update(values, comments)

    def check_settings(self, group_name, values, comments):
        group = self._groups.get(group_name, SettingsGroup(group_name))
        unused_values, unused_comments = group.compare(values, comments)
        for val in unused_values:
            print(
                f"Unnecessary entry {val} in file {self._filename}, group {group._name}"
            )


class StructuredSession(QObject):
    """Stores settings of different parts of the GUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configs = {}
        self._state = None
        self._filename = kwargs.get("filename", None)
        self.populate_defaults()

    def register_config(self, name: str, valdict: Dict, docdict: Dict):
        if name in self._groups:
            group = self._groups.pop(name)
        else:
            group = SettingsGroup(name)
        group.populate(valdict, docdict)
        self._groups[name] = group

    def populate_defaults(self):
        self._paths["root_directory"] = os.path.expanduser("~")
        self._units["energy"] = "meV"
        self._units["time"] = "fs"
        self._units["distance"] = "ang"
        self._units["reciprocal"] = "1/ang"

    def get_parameter(self, key: str) -> str:
        value = self._parameters.get(key, None)
        return value

    def get_path(self, key: str) -> str:
        value = self._paths.get(key, ".")
        return value

    def set_path(self, key: str, value: str):
        self._paths[key] = value

    def get_unit(self, key: str) -> str:
        value = self._units.get(key, "1")
        return value
