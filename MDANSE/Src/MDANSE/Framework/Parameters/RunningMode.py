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

import multiprocessing
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal, NamedTuple, SupportsInt, TypeVar
from warnings import warn

from MDANSE.Framework.Parameters import Integer, SingleChoice
from MDANSE.Framework.Parameters.Parameters import (
    Configurable,
    ConfigWarning,
    CustomConfig,
)

if TYPE_CHECKING:
    from MDANSE.Framework.Parameters.UtilTypes import Depends

Modes = Literal["single-core", "multi-core", "remote"]


class OldRunningMode(NamedTuple):
    mode: Modes
    n_procs: int


class CPUSlots(Integer):
    def validate(self, value: SupportsInt, deps: Depends, /) -> int:
        value = int(value)
        if value < 0:
            value = min(self.maximum, abs(value))

        return super().validate(value, deps)


class RunningMode(CustomConfig):
    mode = SingleChoice[str, Modes](
        choices=("single-core", "multicore", "remote"), default="single-core"
    )
    n_procs = CPUSlots(minimum=1, maximum=multiprocessing.cpu_count(), default=1)

    def validate(self, desc, value):
        if desc.name == "n_procs" and self.mode == "single-core" and value > 1:
            warn(
                "Requested more than one process for single-core job.",
                category=ConfigWarning,
                stacklevel=2,
            )
        return value

    def set(
        self,
        mode: Modes = "single-core",
        n_procs: int = 1,
    ):
        self.mode = mode
        self.n_procs = n_procs

    def __set__(self, owner: Configurable, value: tuple | dict):
        self.owner = owner
        match value:
            case int():
                self.n_procs = value
            case str():
                self.mode = value
            case dict():
                self.set(**value)
            case Sequence():
                self.set(*value)
            case RunningMode():
                self.configuration = value.configuration
            case _:
                super().__set__(owner, value)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(mode={self.mode!r}, n_procs={self.n_procs})"
