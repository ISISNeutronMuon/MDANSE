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

import re
from itertools import islice
from typing import TYPE_CHECKING

import numpy as np
from more_itertools import ilen, split_at

from .Parser import Parser

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import numpy.typing as npt


class XYZFile(Parser):
    """Reads information from an XYZ file.

    This class loads the contents of an XYZ file.
    This file may contain the atom positions, velocities or forces.
    In either case there will be 3 components per atom.

    If you have an ExtendedXYZ file, load it with the ASE converter instead.
    """

    ts_re = re.compile(r"i =.*, time =(.*), E =.*")

    @property
    def n_atoms(self) -> int:
        return self._n_atoms

    def __init__(self, filename: Path | str):
        super().__init__(filename)

        with open(self.filename, encoding="utf-8") as xyz_file:
            self._n_atoms = int(next(xyz_file))
            comment = next(xyz_file)  # Comment line
            atom_block = islice(xyz_file, self.n_atoms)

            self.atoms = [line.strip().split(maxsplit=1)[0] for line in atom_block]
            next(xyz_file)
            comment_2 = next(xyz_file)

        if (match := self.ts_re.search(comment)) and (
            match_2 := self.ts_re.search(comment_2)
        ):
            self.time_step = float(match_2[1]) - float(match[1])
        elif match:
            self.time_step = float(match[1])
        else:
            self.time_step = None

    @property
    def n_frames(self) -> int:
        with open(self.filename, encoding="utf-8") as xyz_file:
            file = map(str.strip, xyz_file)

            file = split_at(file, str.isnumeric)
            file = filter(None, file)

            return ilen(file)

    @property
    def frames(self) -> Iterator[npt.NDArray[float]]:
        with open(self.filename, encoding="utf-8") as xyz_file:
            file = map(str.strip, xyz_file)

            file = split_at(file, str.isnumeric)
            file = filter(None, file)
            yield from map(self.read_step, file)

    @property
    def element_list(self) -> list[str]:
        return self.atoms

    @staticmethod
    def read_step(frame: list[str]) -> npt.NDArray[float]:
        """Reads and returns an array of atom coordinates the next simulation frame."""
        return np.loadtxt(frame[1:], usecols=(1, 2, 3), dtype=np.float64)
