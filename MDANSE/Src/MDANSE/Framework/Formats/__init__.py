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

from enum import Enum, auto

from .FileInMemory import FileInMemory as FileInMemory
from .HDFFormat import HDFFormat as HDFFormat
from .IFormat import IFormat as IFormat
from .MDAFormat import MDAFormat as MDAFormat
from .MDTFormat import MDTFormat as MDTFormat
from .TextFormat import TextFormat as TextFormat


class OutputFormats(Enum):
    MDAFormat = auto()
    TextFormat = auto()
    FileInMemory = auto()
    MDTFormat = auto()

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return None

        for member in cls:
            if member.name == value:
                return member
