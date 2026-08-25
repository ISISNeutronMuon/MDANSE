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
from typing import Any, Generic, TypeVar

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Parsers import Parser

from .InputFileConfigurator import InputFileConfigurator

P = TypeVar("P", bound=Parser)

@IConfigurator.register("FileWithAtomDataConfigurator")
class FileWithAtomDataConfigurator(InputFileConfigurator, Generic[P]):
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

    def __init__(self, *args, parser: type[P] | Callable[[str], P], **kwargs):
        super().__init__(*args, **kwargs)

        self.parser_instance = None
        self.parser = parser

    def configure(self, value: str) -> None:
        """
        Parameters
        ----------
        value : str
            The file path.
        """
        self._original_input = value
        super().configure(value)

        if self.error_status != "OK":
            return

        if self.optional and not value:
            self._original_input = value
            self["value"] = value
            self["filename"] = value
            self.parser_instance = None
            self.error_status = "OK"
            return

        try:
            self.parser_instance = self.parser(value)
        except Exception as e:
            self.error_status = f"File parsing error {e}: {traceback.format_exc()}."
            return

        if not self.labels:
            self.error_status = "Unable to generate atom labels."
            return

    @property
    def frames(self) -> Iterable[Any]:
        """Yield frames."""
        if not self.parser_instance:
            return ()
        return self.parser_instance.frames

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Yields atom labels"""
        if not self.parser_instance:
            return ()
        return self.parser_instance.atom_labels

    @property
    def labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        if not self.parser_instance:
            return []
        return self.parser_instance.labels
