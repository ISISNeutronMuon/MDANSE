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

import traceback
from collections.abc import Callable, Iterable
from typing import Any

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Parsers import Parser

from .InputFileConfigurator import InputFileConfigurator


class FileWithAtomDataConfigurator(InputFileConfigurator):
    """
    Class for handling files that contain atom information.

    Returns the parsed structure in the ``instance`` attribute.

    If this is ``optional`` and undefined, ``instance`` will instead be
    ``None`` for easy checking.

    Parameters
    ----------
    parser : type[Parser] or Callable
        Routine or object to parse data into relevant form.

    Notes
    -----
    For old behaviour any object subclassing this can pass ``self.parse`` into the
    ``parser`` argument.
    """

    def __init__(self, *args, parser: type[Parser] | Callable[[str], Parser], **kwargs):
        super().__init__(*args, **kwargs)

        self.instance = None
        self.parser = parser

    def configure(self, filepath: str) -> None:
        """
        Parameters
        ----------
        filepath : str
            The file path.
        """
        self._original_input = filepath
        super().configure(filepath)

        if self.error_status != "OK":
            return

        if self.optional and not filepath:
            self._original_input = filepath
            self["value"] = filepath
            self["filename"] = filepath
            self.instance = None
            self.error_status = "OK"
            return

        try:
            self.instance = self.parser(filepath)
        except Exception as e:
            self.error_status = f"File parsing error {e}: {traceback.format_exc()}."
            return

        if not self.labels:
            self.error_status = "Unable to generate atom labels."
            return

    @property
    def frames(self) -> Iterable[Any]:
        """Yield frames."""
        return self.instance.frames

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Yields atom labels"""
        return self.instance.atom_labels

    @property
    def labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        return self.instance.labels
