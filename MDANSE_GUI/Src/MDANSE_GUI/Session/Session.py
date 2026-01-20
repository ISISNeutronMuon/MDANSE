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

import json
from abc import abstractmethod
from pathlib import Path
from typing import Any

from qtpy.QtCore import QObject, Signal, Slot

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.Settings import LocalSettings, Settings, UserSettingsModel

json_encoder = json.encoder.JSONEncoder()
json_decoder = json.decoder.JSONDecoder()


class Session(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._models = {}
        self._configs = {}
        self._reserved_filenames = []
        self._state = None

    @abstractmethod
    def connect_settings_file(self, name: str) -> Settings: ...

    @abstractmethod
    def save(self, filename: Path | str | None) -> None: ...

    @abstractmethod
    def load(self, filename: Path | str | None) -> None: ...

    def settings_model(self, settings_filename: str):
        if settings_filename not in self._models:
            LOG.debug(f"session connecting to {settings_filename} for the first time")
            self.connect_settings_file(settings_filename)
        model = self._models[settings_filename]
        LOG.debug(f"session re-using the model {settings_filename}")
        self._configs[settings_filename].load_settings()
        model.refresh()
        return model

    def obtain_settings(self, gui_element):
        try:
            name = gui_element._name
        except AttributeError:
            name = self._main_config_name

        try:
            sf = self._configs[name]
        except KeyError:
            sf = self.connect_settings_file(name)

        sf.load_settings()

        try:
            setting_groups = gui_element.grouped_settings()
        except AttributeError:
            LOG.debug(
                f"GUI element {gui_element} did not have a grouped_settings method."
            )
            return sf

        for gname, (settings, comments) in setting_groups.items():
            LOG.debug(f"Initialising values in {gname}")
            sf.extend_settings(gname, settings, comments)
            sf.check_settings(gname, settings, comments)

        sf.save_values()
        return sf

    def populate_defaults(self):
        gs = self.connect_settings_file(self._main_config_name)
        gs.load_settings()
        paths = gs.group("paths")
        paths.set_group_comment("Lookup of working directory paths for the main GUI")
        paths.add(
            "root_directory", str(Path.home()), "Starting path for any file search"
        )

        units = gs.group("units")
        units.set_group_comment(
            "The GUI will, where possible and indicated, use these physical units."
        )
        units.add("energy", "meV", "The unit of energy preferred by the user.")
        units.add("time", "fs", "The unit of time preferred by the user.")
        units.add("distance", "ang", "The unit of distance preferred by the user")
        units.add(
            "reciprocal", "1/ang", "The momentum (transfer) unit preferred by the user"
        )

        gs.save_values()

    def get_path(self, key: str) -> str:
        settings = self._configs[self._main_config_name]
        group = settings["paths"]
        value = group.get(key, Path.cwd())
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

    def main_settings(self):
        return self._configs[self._main_config_name]

    def reserved_filenames(self) -> list[Path]:
        return self._reserved_filenames

    @Slot(str)
    def protect_filename(self, some_filename: str):
        new_filename = Path(some_filename).absolute()
        self._reserved_filenames.append(new_filename)

    @Slot(str)
    def free_filename(self, some_filename: str):
        filename = Path(some_filename).absolute()

        if filename in self._reserved_filenames:
            self._reserved_filenames.remove(filename)


class StructuredSession(Session):
    """Stores settings of different parts of the GUI."""

    def __init__(self, *args, filename: str = "mdanse_general_settings", **kwargs):
        super().__init__(*args, **kwargs)
        self._main_config_name = filename
        self._filename = filename
        self.populate_defaults()

    def connect_settings_file(self, name: str):
        model = UserSettingsModel(settings=name)
        sf = model._settings
        self._configs[name] = sf
        self._models[name] = model
        return sf

    @Slot()
    def save(self):
        for config in self._configs.values():
            config.save_values()

    def load(self, fname: str | None = None):
        """Included for compatibility with LocalSession only.
        Now each component loads its own config separately."""


class LocalSession(Session):
    """Stores different parameters, and the state
    of the software.

    The intention is to have a single session that
    can be accessed by different tabs.

    At the moment, LocalSession is meant to be used
    for testing individual GUI components, and
    is largely a mock object.
    """

    new_units = Signal(dict)
    new_cmap = Signal(str)

    def __init__(self, *args, filename: str = "mdanse_general_settings", **kwargs):
        super().__init__(*args, **kwargs)

        self._main_config_name = filename
        self._filename = filename
        self._parameters = {}
        self._state = None
        self._filename = None
        self.populate_defaults()

    def connect_settings_file(
        self, name: str, *, settings: dict[str, Any] | None = None
    ):
        if settings is None:
            settings = {}

        model = LocalSettings(settings=settings)
        self._configs[name] = model._settings
        self._models[name] = model
        return model._settings

    @Slot()
    def save(self, fname: str | None = None):
        if fname is None:
            if self._filename is None:
                fname = PLATFORM.application_directory() / "gui_session.json"
            else:
                fname = self._filename

        try:
            with open(fname, "w") as target:
                json.dump(self._configs, target, cls=json_encoder)
        except Exception:
            return

        self._filename = fname

    def load(self, fname: Path | str | None = None) -> None:
        if fname is None:
            fname = PLATFORM.application_directory() / "gui_session.json"
        fname = Path(fname)

        try:
            with fname.open("r") as inp:
                all_items = json.load(inp, cls=json_decoder)
        except Exception:
            LOG.warning(f"Failed to read session settings from {fname}")
            return

        for key, values in all_items.items():
            self.connect_settings_file(key, settings=values)
        self._filename = fname
