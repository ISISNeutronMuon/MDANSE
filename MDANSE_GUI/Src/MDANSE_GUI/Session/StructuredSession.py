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
import tomlkit
from tomlkit.parser import ParseError
from tomlkit.toml_file import TOMLFile

from MDANSE import PLATFORM
from MDANSE.Framework.Units import measure, unit_lookup


class SettingsGroup:

    def __init__(self, group_name: str) -> None:
        self._name = group_name
        self._settings = {}
        self._comments = {}
        self._group_comment = ""

    def set_comment(self, comment: str):
        self._group_comment = comment

    def add(self, varname: str, value: str, comment: str):
        self._settings[varname] = value
        self._comments[varname] = comment

    def set(self, varname: str, value: str):
        if not varname in self._settings:
            print(
                f"Group {self._name} has no entry {varname}. Add it first using add()."
            )
            return False
        self._settings[varname] = value

    def get(self, varname: str):
        return self._settings[varname]

    def populate(self, settings: Dict, comments: Dict):
        for key, value in settings.items():
            self._settings[key] = value
            self._comments[key] = comments.get(key, "---")

    def update(self, settings: Dict, comments: Dict):
        for key, value in settings.items():
            if key in self._settings:
                continue
            self._settings[key] = value
            self._comments[key] = comments.get(key, "---")

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
                self._groups[key] = group

    def keys(self):
        return self._groups.keys()

    @property
    def groups(self):
        return self._groups

    def group(self, group_name: str) -> "SettingsGroup":
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
        self._file.write(newdoc)

    def overwrite_settings(self, group_name, values, comments):
        group = self.group(group_name)
        group.populate(values, comments)

    def extend_settings(self, group_name, values, comments):
        group = self.group(group_name)
        group.update(values, comments)

    def check_settings(self, group_name, values, comments):
        group = self.group(group_name)
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
        self._main_config_name = "mdanse_general_settings"
        self._filename = kwargs.get("filename", self._main_config_name)
        self.populate_defaults()

    @Slot()
    def save(self, fname: str = None):
        for name, config in self._configs.items():
            config.save_values()

    def load(self, fname: str = None):
        """Included for compatibility with LocalSession only.
        Now each component loads its own config separately."""

    def obtain_settings(self, gui_element):
        try:
            name = gui_element._name
        except AttributeError:
            name = self._main_config_name
        try:
            sf = self._configs[name]
        except KeyError:
            sf = SettingsFile(name)
            self._configs[name] = sf
        sf.load_from_file()
        try:
            setting_groups = gui_element.grouped_settings()
        except AttributeError:
            pass
        else:
            for group in setting_groups:
                gname, settings, comments = group[0], group[1], group[2]
                sf.extend_settings(gname, settings, comments)
                sf.check_settings(gname, settings, comments)
            sf.save_values()
        return sf

    def populate_defaults(self):
        gs = SettingsFile(self._main_config_name)
        paths = gs.group("paths")
        paths.set_comment("Lookup of working directory paths for the main GUI")
        units = gs.group("units")
        units.set_comment(
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
        gs.load_from_file()
        gs.save_values()
        self._configs[self._main_config_name] = gs

    def get_path(self, key: str) -> str:
        settings = self._configs[self._main_config_name]
        group = settings["paths"]
        value = group.get(key, ".")
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
