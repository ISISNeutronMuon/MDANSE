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

from mdtraj.utils import ilen
from more_itertools import all_equal, first

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Parsers import Parser

from .MultiInputFileConfigurator import MultiInputFileConfigurator

P = TypeVar("P", bound=Parser)


@IConfigurator.register("MultiFileWithAtomDataConfigurator")
class MultiFileWithAtomDataConfigurator(MultiInputFileConfigurator, Generic[P]):
    """
    Class for handling multiple files that contain atom information.

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

        self.parser_instances: dict[str, P] = {}
        self.parser = parser

    def configure(self, value: str | list[str]) -> None:
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
            self["filenames"] = value
            self.parser_instances.clear()
            self.error_status = "OK"
            return

        try:
            self.parser_instances: dict[str, P] = {
                value:
                self.parser(value) for value in self["values"]
            }
        except Exception as e:
            self.error_status = f"File parsing error {e}: {traceback.format_exc()}."
            return

        if not all_equal(ilen(p.frames) for p in self.parser_instances.values()):
            self.error_status = "Frame length mismatch."
            return

        if not self.labels:
            self.error_status = "Unable to generate atom labels."
            return

    @property
    def n_frames(self) -> int:
        """Number of frames."""
        return ilen(first(self.parser_instances.values()).frames)

    @property
    def filenames(self) -> Iterable[str]:
        yield from self["filenames"]

    @property
    def frames(self) -> Iterable[Any]:
        """Yield frames."""
        yield from zip(*(p.frames for p in self.parser_instances.values()), strict=False)

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Yields atom labels"""
        for parser in self.parser_instances.values():
            yield from parser.atom_labels

    @property
    def labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        return list({label for p in self.parser_instances.values() for label in p.labels})
