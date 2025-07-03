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
import importlib
from enum import Enum, auto
from pathlib import Path


class OutputFormats(Enum):
    MDAFormat = auto()
    TextFormat = auto()
    FileInMemory = auto()

    MDTFormat = auto()

    @classmethod
    def _missing_(cls, value: str | int):
        for member in cls:
            if (isinstance(value, str) and member.name == value) or (isinstance(value, int) and member.value == value):
                return member

current_path = Path(__file__).parent

modnames = (
    fname.stem for fname in current_path.glob("*.py") if fname.stem != "__init__"
)
globdict = globals()

for name in modnames:
    try:
        tempmod = importlib.import_module("." + name, "MDANSE.Framework.Formats")
    except ModuleNotFoundError:
        continue
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module
