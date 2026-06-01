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

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, NamedTuple, TypedDict, TypeVar, cast

import numpy as np
from ase.io.formats import ioformats

from MDANSE.Framework.Formats import OutputFormats
from MDANSE.Framework.Parameters.BaseTypes import Integer, PathParam
from MDANSE.Framework.Parameters.Choices import MultipleChoice, SingleChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    CustomConfig,
)
from MDANSE.MLogging import LogLevels
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

if TYPE_CHECKING:
    from pathlib import Path

Self = TypeVar("Self", bound="OutputFile")


class OldOutputSettings(NamedTuple):
    path: Path | str = ""
    out_format: OutputFormats | str | int | Iterable[OutputFormats | str | int] = (
        "MDAFormat",
        "TextFormat",
    )
    log_level: LogLevels | int | str = "None"


class OldTrajectorySettings(NamedTuple):
    path: Path | str
    dtype: int
    chunk_size: int
    compression: str
    out_format: OutputFormats | str | int | Iterable[OutputFormats | str | int]
    log_level: LogLevels | int | str


class OutputFormat(MultipleChoice[OutputFormats | str | int, OutputFormats]):
    def __init__(
        self,
        allowed_formats: Iterable[OutputFormats | str | int],
        **kwargs,
    ):
        allowed_formats = cast(
            "map[OutputFormats]", map(OutputFormats, allowed_formats)
        )
        super().__init__(
            n_choices=None,
            choices=set(allowed_formats),
            aliases={x.name: x for x in OutputFormats}
            | {x.value: x for x in OutputFormats},
            **kwargs,
        )


class OutputFile(CustomConfig):
    path = PathParam(mode="w")
    out_format = OutputFormat(
        ("MDAFormat", "TextFormat", "FileInMemory"), default=("MDAFormat", "TextFormat")
    )
    log_level = SingleChoice[LogLevels | int | str, LogLevels](
        choices=LogLevels,
        default=LogLevels.NONE,
        label="Reporting log level.",
    )

    NAMES = ("path", "out_format", "log_level")

    @property
    def root(self) -> Path:
        return self.path.with_suffix("")

    @property
    def write_logs(self) -> bool:
        return self.log_level is not None

    def set(
        self,
        path: Path | str = "",
        out_format: Iterable[OutputFormats | str | int] = ("MDAFormat", "TextFormat"),
        log_level: LogLevels | int | str = LogLevels.NONE,
    ) -> None:
        """Set values from old-style tuple."""
        self.path = path
        self.out_format = out_format
        self.log_level = log_level

    def set_from_self(self, other) -> None:
        """Set from a like-object."""
        if other.NAMES != self.NAMES:
            raise ConfigError(
                f"Type mismatch: {type(self).__name__} vs {type(other).__name__}"
            )

        for arg in self.NAMES:
            setattr(self, arg, getattr(other, arg))

    def __set__(self, owner: Configurable, value: dict | Sequence | Self) -> None:
        self.owner = owner

        match value:
            case str():
                self.set(value)
            case dict():
                self.set(**value)
            case Sequence():
                self.set(*value)
            case _:
                self.set_from_self(value)

    def __str__(self) -> str:
        try:
            return str(self.path)
        except ConfigError:
            return f"{type(self).__name__}(Undefined or invalid)"

    def __repr__(self) -> str:
        try:
            return f"{type(self).__name__}({self.path!r}, {self.out_format})"
        except ConfigError:
            return f"{type(self).__name__}(Undefined or invalid)"


def add_mdt(_desc, value, _deps):
    """Add .mdt to filepath."""
    return value.with_suffix(".mdt")


class OutputTrajectory(OutputFile):
    path = PathParam(
        mode="w",
        extensions={"MDANSE Trajectory": "*.mdt"},
        on_set=add_mdt,
    )
    out_format = OutputFormat(
        ("MDTFormat",),
        default=("MDTFormat",),
    )
    dtype = SingleChoice(
        choices=(np.float16, np.float32, np.float64),
        default=np.float64,
        aliases=(
            dict.fromkeys(("64", "float64", "float", float, 64), np.float64)
            | dict.fromkeys(("32", "float32", "single", 32), np.float32)
            | dict.fromkeys(("16", "float16", "half", 16), np.float16)
        ),
    )
    chunk_size = Integer(minimum=32, maximum=65536, default=128)
    compression = SingleChoice(
        choices=("none", *TrajectoryWriter.allowed_compression), default="none"
    )

    NAMES = ("path", "dtype", "chunk_size", "compression", "log_level")

    def set(
        self,
        path: Path | str = "",
        dtype: int | str = "64",
        chunk_size: int = 128,
        compression: str = "none",
        log_level: LogLevels = LogLevels.NONE,
        out_format: None = None,
    ) -> None:
        """Set values from old-style tuple."""
        self.path = path
        self.dtype = dtype
        self.chunk_size = chunk_size
        self.compression = compression
        self.log_level = log_level

    @property
    def dtype_size(self) -> int:
        return int(str(self.dtype)[-4:-2])

    @property
    def configuration(self) -> dict[str, Any]:
        return super().configuration() | {
            "dtype": self.dtype_size,
            "chunk_size": self.chunk_size,
            "compression": self.compression,
        }


class ASEOutputFormat(OutputFile):
    out_format = SingleChoice[str, str](
        choices=(key for key, val in ioformats.items() if val.can_write),
        default=("vasp",),
    )
