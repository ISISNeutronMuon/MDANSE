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

from collections.abc import Collection, Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from MDANSE.Framework.Formats import OutputFormats
from MDANSE.MLogging import LogLevels
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

from .AbsConfigDesc import ConfigError, ConfigureDescriptor
from .BaseTypesDescriptor import IntegerConfigDesc, PathConfigDesc
from .ChoiceConfigDesc import MultipleChoiceConfigDesc, SingleChoiceConfigDesc


class LogLevelConfigDesc(SingleChoiceConfigDesc):
    def __init__(self, **kwargs):
        super().__init__(choices={level.name for level in LogLevels}, **kwargs)

    def validate(self, value: LogLevels | int | str, *_deps) -> LogLevels:
        try:
            value = LogLevels(value)
        except Exception as err:
            raise ConfigError("Invalid config level.") from err


class OutputFormatConfigDesc(MultipleChoiceConfigDesc):
    def __init__(
        self,
        allowed_formats: Iterable[OutputFormats | str | int],
        **kwargs,
    ):
        allowed_formats = map(OutputFormats, allowed_formats)
        super().__init__(
            n_choices=None,
            choices={format.name for format in allowed_formats},
            **kwargs,
        )


class OutputFileConfigDesc:
    out_format = OutputFormatConfigDesc(("MDAFormat", "TextFormat"))
    log_level = LogLevelConfigDesc(default=LogLevels.NONE, label="Reporting log level.")
    path = PathConfigDesc(mode="w")

    def __init__(
        self,
        formats: Iterable[OutputFormats | str | int] = ("MDAFormat", "TextFormat"),
        level: LogLevels = LogLevels.NONE,
        **kwargs,
    ):
        ConfigureDescriptor.__init__(self, **kwargs)
        self.log_level = level
        self.out_format = formats

    @property
    def root(self) -> Path:
        return self.path.with_suffix("")

    @property
    def write_logs(self) -> bool:
        return self.log_level is not None

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.path=}, {self.out_format=}, {self.log_level=})"


class OutputFilePlusMemConfigDesc(OutputFileConfigDesc):
    out_format = OutputFormatConfigDesc(("MDAFormat", "TextFormat", "FileInMemory"))


class OutputTrajectoryConfigDesc(OutputFileConfigDesc):
    out_format = OutputFormatConfigDesc(
        ("MDTFormat",),
    )
    dtype = SingleChoiceConfigDesc(choices=(np.float16, np.float32, np.float64), default=np.float64)
    chunk_size = IntegerConfigDesc(minimum=32, maximum=65536, default=128)
    compression = SingleChoiceConfigDesc(
        choices=("none", *TrajectoryWriter.allowed_compression), default="none"
    )

    def __init__(
        self,
        level: LogLevels = LogLevels.NONE,
        dtype: int | str | None = None,
        chunk_size: int | None = None,
        compression: str = "none",
        **kwargs,
    ):
        super().__init__(formats=("MDTFormat",), level=level, **kwargs)
        if dtype is not None:
            self.dtype = str(dtype)
        if chunk_size is not None:
            self.chunk_size = chunk_size
        self.compression = self.compression

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.path=}, {self.log_level=}, {self.dtype=}, {self.chunk_size=}, {self.compression=})"
