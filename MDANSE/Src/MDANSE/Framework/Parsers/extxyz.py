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
from pathlib import Path

from more_itertools import ilen

from MDANSE.Framework.Parsers.Parser import Parser

try:
    import extxyz

    extxyz_available = True
except ImportError:
    extxyz_available = False



class ExtXYZFile(Parser):

    def __init__(self, filename: Path | str):
        self.filename = filename
        frame = next(self.frames)
        print(frame.info, frame.arrays)


    @cached_property
    def n_atoms(self) -> int:
        frame = extxyz.read_dicts(self.filename, index=0)
        return frame.natoms

    @cached_property
    def n_frames(self) -> int:
        return ilen(extxyz.iread_dicts(self.filename))

    @cached_property
    def element_list(self) -> list[str]:
        frame = extxyz.read_dicts(self.filename, index=0)
        return frame.arrays["species"]

    @property
    def frames(self) -> Iterator[extxyz.Frame]:
        yield from extxyz.iread_dicts(self.filename)
