#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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
from typing import Any, ClassVar, NamedTuple

from MDANSE.Core.RegisterFactory import RegisterFactory
from MDANSE.IO.IOUtils import UCDict
from MDANSE.util_types import FloatArray


class Operation(NamedTuple):
    name: str
    target: str
    params: str


class Op(RegisterFactory, ABC):
    registry: ClassVar[UCDict[str, type[Op]]] = UCDict()

    def __init__(self, target: str) -> None:
        self.target = target

    @property
    @abstractmethod
    def params(self) -> dict[str, Any]: ...

    @classmethod
    @abstractmethod
    def param_types(cls) -> dict[str, type]: ...

    @property
    def param_str(self) -> str:
        return ",".join(f"{name}={val}" for name, val in self.params.items())

    @classmethod
    def from_param_str(cls, params: str) -> dict[str, Any]:
        out = {}

        for param_str, typ in zip(
            params.split(","), cls.param_types().values(), strict=False
        ):
            param, val = param_str.split("=")
            out[param] = typ(val)

        return out

    @property
    def as_tuple(self) -> Operation:
        return Operation(type(self).__name__, self.target, self.param_str)

    @abstractmethod
    def apply_single(self, dataset: FloatArray): ...

    @classmethod
    def from_tuple(cls, op: Operation) -> Op:
        new = cls.instance(op.name)
        params = new.from_param_str(op.params)

        return new(op.target, **params)
