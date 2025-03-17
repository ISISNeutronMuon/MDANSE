#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

import json
from pathlib import Path
from typing import Any, Optional

import h5py

from MDANSE import PLATFORM
from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory

DEFAULT_DATABASE = (
    PLATFORM.base_directory() / "MDANSE" / "Framework" / "selection_storage.json"
)

USER_DATABASE = PLATFORM.application_directory() / "selection_storage.json"


class SingleEntry:
    """A ReusableSelection together with its usage statistics."""

    def __init__(self, json_string: Optional[str] = None, name: Optional[str] = None):
        """Create an emtpy entry in the selection database.

        Parameters
        ----------
        json_string : Optional[str], optional
            The input to a ReusableSelection, by default None
        name : Optional[str], optional
            string label of the selection in the database, by default None

        """
        self.data_fields = ["name", "json_string"]
        self.name = name
        self.json_string = json_string

    def from_dictionary(self, saved_values: dict[str, Any]):
        """Set values from a dictionary, typically loaded from file."""
        for key, value in saved_values.items():
            setattr(self, key, value)
            self.data_fields.append(key)

    def to_json(self) -> str:
        """Save all the data fields as a single dictionary in a JSON string."""
        results = {key: getattr(self, key, "") for key in self.data_fields}
        return json.dumps(results)


class SelectionStorage:
    """Stores atom selection logic used most often by the users."""

    def __init__(self, filename: Optional[str] = None):
        """Create a backend for finding selection strings.

        Parameters
        ----------
        filename : Optional[str], optional
            Name of a non-standard file from which to load selections, by default None

        """
        self._named_entries = {}
        self._unnamed_entries = []
        self.load_from_file(DEFAULT_DATABASE)
        if not filename:
            self.load_from_file(USER_DATABASE)
        else:
            self.load_from_file(filename)

    def load_from_file(self, filename: str):
        """Populate the internal list with entries from a file.

        If an entry with a specific key already exists, it will
        be overwritten.

        Parameters
        ----------
        filename : str
            name of the file containing the selection definitions

        """
        path = Path(filename)
        if not path.exists():
            LOG.warning(
                f"File {filename} was not found." "Atoms selections will not be loaded."
            )
            return
        with path.open() as source:
            entries = json.load(source)
        for entry_dict in entries:
            temp_entry = SingleEntry()
            temp_entry.from_dictionary(entry_dict)
            if name_str := entry_dict["name"]:
                self._named_entries[name_str] = temp_entry
            else:
                self._unnamed_entries.append(temp_entry)

    def save_to_file(self, filename: str):
        """Write all entires to the specified file.

        Parameters
        ----------
        filename : str
            Path to the file where the selections will be saved.

        """
        path = Path(filename)
        with path.open("w") as target:
            target.write(json.dumps(self._named_entries))
            target.write(json.dumps(self._unnamed_entries))
