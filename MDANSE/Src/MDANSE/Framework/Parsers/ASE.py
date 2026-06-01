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

from collections.abc import Iterator
from functools import cached_property
from typing import TYPE_CHECKING, overload

from ase.io import iread, read
from ase.io.trajectory import Trajectory as ASETrajectory

from MDANSE.Framework.AtomMapping import AtomLabel

from .Parser import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from ase import Atoms

SLICE_ALL = slice(None)


class ASEParser(Parser):
    def __init__(self, filename: Path | str, format: str | None = None):
        super().__init__(filename)
        self.format = format

    @property
    def as_trajectory(self):
        return ASETrajectory(self.filename)

    @overload
    def __getitem__(self, key: int) -> Atoms: ...

    @overload
    def __getitem__(self, key: slice) -> list[Atoms]: ...

    @overload
    def __getitem__(self, key: str) -> list[Atoms] | Atoms: ...

    def __getitem__(self, key: int | slice | str) -> list[Atoms] | Atoms:
        return read(self.filename, index=key, format=self.format)

    def frame_subset(self, selection: slice | str = SLICE_ALL) -> Iterable[Atoms]:
        """Return an iterator over a slice of frames."""
        return iread(self.filename, index=selection, format=self.format)

    @property
    def frames(self) -> Iterable[Atoms]:
        """Return an iterator over all frames."""
        return iread(self.filename, index=":", format=self.format)

    @cached_property
    def element_list(self) -> list[str]:
        """Return list of elements."""
        return self[0].get_chemical_symbols()
