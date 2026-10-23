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
from __future__ import annotations

import copy
import json
from collections import ChainMap
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton
from MDANSE.IO.IOUtils import json_handler

if TYPE_CHECKING:
    from collections.abc import ItemsView


class Database(metaclass=Singleton):
    """Base class for all the databases."""

    _DEFAULT_DATABASE: ClassVar[Path]
    _LOCAL_PATH: ClassVar[Path]

    @property
    def _USER_DATABASE(self) -> Path:
        return PLATFORM.application_directory / self._LOCAL_PATH

    def __init__(self):
        self._data = {}
        self._default_data = {}
        self.data = ChainMap(self._data, self._default_data)
        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def _load(
        self,
        user_database: Path | str | None = None,
        default_database: Path | str | None = None,
    ) -> None:
        """Load the atom database from the pre-defined paths.

        This method should never be called elsewhere than __init__ or unit testing.

        Parameters
        ----------
        user_database : Path | str | None, optional
            The path to the user-defined database. If None, built-in path is used.
        default_database : Path | str | None, optional
            The path to the MDANSE atom database. If None, built-in path is used.

        """
        self._user_database = (
            Path(user_database) if user_database is not None else self._USER_DATABASE
        )
        default_database = (
            Path(default_database)
            if default_database is not None
            else self._DEFAULT_DATABASE
        )

        self._default_data: dict[str, Any] = json_handler(default_database)
        self._data: dict[str, Any] = (
            json_handler(self._user_database) if self._user_database.exists() else {}
        )
        self.data = ChainMap(self._data, self._default_data)

    def __iter__(self):
        """Return a generator over the entries stored in the database."""
        for v in self.data.values():
            yield copy.deepcopy(v)

    def items(self) -> ItemsView[str, dict]:
        """Return the iterator over the items of the data dict.

        Allows for iteration over particle names and their data
        simultaneously.

        Returns
        -------
        ItemsView[str, dict]
            dict_items iterator of the internal dictionary.

        """
        return self.data.items()

    def _reset(self) -> None:
        """Reset the database, removing all data."""
        self.data.clear()

    def save(self) -> None:
        """Save a copy of the database to MDANSE application directory.

        This database will then be used in the future.
        If the user database already exists, calling this function will overwrite it.
        """
        with open(self._USER_DATABASE, "w") as f:
            json.dump(dict(self.data.maps[0]), f, indent=4)
