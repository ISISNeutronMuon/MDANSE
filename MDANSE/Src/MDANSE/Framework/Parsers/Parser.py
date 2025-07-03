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
from collections.abc import Collection, Iterable, Iterator
from pathlib import Path

from MDANSE.Framework.AtomMapping import AtomLabel


class Parser(ABC):
    def __init__(self, filename: Path | str, **kwargs):
        self.filename = Path(filename).expanduser()

    @property
    @abstractmethod
    def frames(self) -> Iterator:
        """Return all frames contained in the file as a sequential iterator."""

    @property
    @abstractmethod
    def element_list(self) -> Collection[str]:
        """Return a list of elements in the structure."""

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
