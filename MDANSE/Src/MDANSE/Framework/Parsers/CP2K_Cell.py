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

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from more_itertools import ilen, take

from .Parser import Parser

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator


class CellFileError(Exception):
    pass


class CP2KCellFile(Parser):
    """Opens and reads the CP2K cell file.

    The CP2K cell output contains the unit cell size for each simulation step.
    """

    def __init__(self, filename: Path | str):
        self.filename = Path(filename).expanduser()

        with self.filename.open(encoding="utf8") as in_file:
            # Skip the first line
            next(in_file)

            time_steps = []

            for line in take(2, in_file):
                words = line.strip().split()

                try:
                    time_steps.append(float(words[1]))
                except ValueError as err:
                    raise CellFileError(
                        f"Cannot cast time step {words[1]} to a floating point number"
                    ) from err

        if len(time_steps) == 1:
            self.time_step = 0.0
        else:
            self.time_step = time_steps[1] - time_steps[0]

    @property
    def element_list(self) -> Collection[str]:
        return ("du",)

    @property
    def frames(self) -> Iterator:
        with self.filename.open(encoding="utf8") as in_file:
            # Skip the first line
            next(in_file)

            for line in map(str.strip, in_file):
                words = line.split()

                if len(words) != 12:
                    raise CellFileError(f"Invalid format for cell line: {line}")

                _step, _ts, unit_cell, _volume = (
                    int(words[0]),
                    float(words[1]),
                    np.array(words[2:11], dtype=np.float64),
                    float(words[11]),
                )
                unit_cell = unit_cell.reshape(3, 3)
                yield unit_cell

    @property
    def n_frames(self) -> int:
        return ilen(self.frames)
