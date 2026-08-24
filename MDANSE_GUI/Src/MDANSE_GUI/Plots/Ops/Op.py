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
from asyncio import run
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, NamedTuple, Protocol, runtime_checkable

from typing_extensions import Self, TypeIs

from MDANSE.Core.RegisterFactory import RegisterFactory
from MDANSE.IO.IOUtils import UCDict
from MDANSE.util_types import FloatArray
from MDANSE_GUI.Utils import parse_token


class Operation(NamedTuple):
    name: str
    target: str
    params: str


@runtime_checkable
class PreApply(Protocol):
    def pre_calculate(self, datasets: Iterable[FloatArray]) -> None:
        """Pre-compute some values from all targets before applying to data."""


@runtime_checkable
class HasStats(Protocol):
    """Operation with statistics to display."""

    STATS: ClassVar[tuple[str, ...]]

    @property
    def stats(self) -> dict[str, str]:
        """Calculate some statistics for display."""


@runtime_checkable
class HasStatsSingle(HasStats, Protocol):
    """Operation with per dataset statistics to display."""

    def stats_calculate_single(self, datasets: FloatArray) -> None:
        """Pre-compute some values for display in transform widget."""


@runtime_checkable
class HasStatsMult(HasStats, Protocol):
    """Operation with global statistics to display."""

    def stats_calculate(self, datasets: Iterable[FloatArray]) -> None:
        """Pre-compute some values for display in transform widget."""


class Op(RegisterFactory["Op"], ABC):
    """Base class for operations."""

    registry: ClassVar[UCDict[str, type[Op]]] = UCDict()
    predictors: ClassVar[tuple[Callable[[], Any], ...]] = ()

    def __init__(self, target: str) -> None:
        self.target = target

    @property
    @abstractmethod
    def params(self) -> dict[str, Any]:
        """Mapping of init kwargs to parameter values."""

    @classmethod
    @abstractmethod
    def param_types(cls) -> dict[str, type]:
        """Mapping of init kwargs to parameter types."""

    @abstractmethod
    def apply_single(self, dataset: FloatArray):
        """Apply the operation to a single dataset."""

    @property
    def param_str(self) -> str:
        """Params dict as string for display."""
        return ",".join(f"{name}={val}" for name, val in self.params.items())

    @classmethod
    def from_param_str(cls, params: str) -> dict[str, Any]:
        """Build operation from parameter string."""
        out = {}

        for param_str, typ in zip(
            params.split(","), cls.param_types().values(), strict=False
        ):
            param, val = param_str.split("=")
            out[param] = typ(val)

        return out

    @property
    def as_tuple(self) -> Operation:
        """Operation as a tuple."""
        return Operation(type(self).__name__, self.target, self.param_str)

    @classmethod
    def from_tuple(cls, op: Operation) -> Op:
        """Construct an operation from it tuple."""
        new = cls.instance(op.name)
        params = new.from_param_str(op.params)

        return new(op.target, **params)

    def targets(self, max_len: int) -> set[int]:
        """Get targets for operation."""
        return set(parse_token(self.target, max_len + 1))
