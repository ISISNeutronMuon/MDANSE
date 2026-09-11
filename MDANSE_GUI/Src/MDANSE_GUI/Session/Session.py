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
from multiprocessing.spawn import _main
from pathlib import Path
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import QObject, Signal, Slot

from MDANSE import PLATFORM
from MDANSE.Core.Settings import Settings
from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.Settings import GUISettings

if TYPE_CHECKING:
    from MDANSE_GUI.TabbedWindow import MDANSEMainWindow
    from MDANSE_GUI.Tabs.GeneralTab import GeneralTab

json_encoder = json.encoder.JSONEncoder()
json_decoder = json.decoder.JSONDecoder()


class Session(QObject):
    def __init__(self, *args, settings: GUISettings | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._settings = settings or GUISettings(save=False)
        self.model = self._settings
        self._reserved_filenames: set[Path] = set()

    def save(self, filename: Path | None = None) -> None:
        Settings.save(filename)

    @abstractmethod
    def load(self, filename: Path | str | None) -> None: ...

    def settings_model(self):
        return self._settings

    def get_path(self, key: str) -> str:
        return Settings.get_opt_w_default("paths", key, str(Path.cwd()))

    def set_path(self, key: str, value: str) -> None:
        self._settings["paths", key] = value

    def get_unit(self, key: str) -> str:
        return Settings.get_opt_w_default("units", key, "N/A")

    @property
    def reserved_filenames(self) -> set[Path]:
        return self._reserved_filenames

    @Slot(str)
    def protect_filename(self, some_filename: str):
        new_filename = Path(some_filename).absolute()
        self._reserved_filenames.add(new_filename)

    @Slot(str)
    def free_filename(self, some_filename: str):
        filename = Path(some_filename).absolute()
        self._reserved_filenames.discard(filename)
