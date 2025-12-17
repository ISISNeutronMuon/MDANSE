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
from pathlib import Path

from MDANSE.MLogging import LOG


class RecentFiles:
    """Stores recently used file names in a JSON file."""

    def __init__(self, file_path: Path, max_file_count: int, placeholder_text: str):
        self.json_file_path = file_path
        self.max_files = max_file_count
        self.placeholder_text = placeholder_text
        self.create_initial_file()

    def create_initial_file(self):
        """Initialise the JSON file with a placeholder text string."""
        if not self.json_file_path.exists():
            with self.json_file_path.open("w", encoding="utf-8") as file:
                json.dump([self.placeholder_text], file, indent=4)

    def store_recently_used_filename(self, loaded_file: str):
        """Updating recent file list with successfully loaded file

        Parameters
        ----------
        loaded_file : str
            Path of the successfully loaded file
        """
        # if the recent file exists and not empty
        recent_files = []

        if self.json_file_path.is_file():
            try:
                with self.json_file_path.open(encoding="utf-8") as file:
                    recent_files = json.load(file)
            except json.decoder.JSONDecodeError as err:
                LOG.error("Invalid recent files json %s: %s", self.json_file_path, err)

        if loaded_file in recent_files:
            recent_files.remove(loaded_file)
        recent_files.append(loaded_file)

        recent_files = recent_files[-self.max_files :]

        with self.json_file_path.open("w", encoding="utf-8") as file:
            json.dump(recent_files, file, indent=4)
