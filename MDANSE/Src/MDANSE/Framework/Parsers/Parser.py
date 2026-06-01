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

from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from more_itertools import ilen

from MDANSE.Framework.AtomMapping import AtomLabel

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator


class Parser(ABC):
    def __init__(self, filename: Path | str, **kwargs):
        self.filename = Path(filename).expanduser()

    def __str__(self) -> str:
        return str(self.filename)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self.filename)!r})"

    def __len__(self) -> int:
        return self.n_frames

    @cached_property
    def n_frames(self) -> int:
        return ilen(self.frames)

    @property
    def n_atoms(self) -> int:
        return len(self.element_list)

    @property
    @abstractmethod
    def frames(self) -> Iterator:
        """Return all frames contained in the file as a sequential iterator."""

    @property
    @abstractmethod
    def element_list(self) -> Collection[str]:
        """Return a list of elements in the structure."""

    @property
    def labels(self) -> list[AtomLabel]:
        return list(set(self.atom_labels))

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Return the set of atom labels.

        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atm_label in self.element_list:
            yield AtomLabel(atm_label)
