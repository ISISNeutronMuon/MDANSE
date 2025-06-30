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

from MDANSE.Formats import OutputFormats
from MDANSE.MLogging import LogLevels
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

from .AbsConfigDesc import ConfigError, ConfigureDescriptor
from .BaseConfigDesc import IntegerConfigDesc, PathConfigDesc
from .ChoiceConfigDesc import MultipleChoiceConfigDesc, SingleChoiceConfigDesc


class LogLevelConfigDesc(SingleChoiceConfigDesc):
    def __init__(self, **kwargs):
        super().__init__(choices={level.name for level in LogLevels.members}, **kwargs)

    def validate(self, value: LogLevels | int | str, *_deps) -> LogLevels:
        try:
            value = LogLevels(value)
        except Exception as err:
            raise ConfigError("Invalid config level.") from err


class OutputFormatConfigDesc(MultipleChoiceConfigDesc):
    def __init__(
        self, formats: Iterable[OutputFormats | int | str] = [0, 1, 2], **kwargs
    ):
        formats = map(OutputFormats, formats)
        super().__init__(
            n_choices=None,
            choices={format.name for format in formats},
            **kwargs,
        )


@dataclass
class OutputFileState:
    filename: Path = Path.cwd() / "DEFAULT_FILENAME"
    formats: Collection[OutputFormats] = [
        OutputFormats.MDAFormat,
        OutputFormats.TextFormat,
        OutputFormats.FileInMemory,
    ]
    logs: LogLevels = LogLevels.NONE


class OutputFileConfigDesc:
    out_format = OutputFormatConfigDesc()
    log_level = LogLevelConfigDesc(default=LogLevels.NONE, label="Reporting log level.")
    out_file = PathConfigDesc(mode="r")

    def __init__(
        self,
        level: LogLevels = LogLevels.NONE,
        formats: Collection[OutputFormats] = tuple(OutputFormats.members),
        *,
        allowed_formats: Collection[OutputFormats] = (),
        **kwargs,
    ):
        if allowed_formats:
            self.__dict__["out_format"].choices = formats

        ConfigureDescriptor.__init__(self, **kwargs)
        self.log_level = level
        self.out_format = formats

    @property
    def write_logs(self) -> bool:
        return self.log_level is not None

class OutputTrajectoryConfigDesc(OutputFileConfigDesc):
    dtype = SingleChoiceConfigDesc(choices=("16", "32", "64"), default="64")
    chunk_size = IntegerConfigDesc(mini=32, maxi=65536, default=128)
    compression = SingleChoiceConfigDesc(choices=("none", *TrajectoryWriter.allowed_compression), default="none")

    def __init__(self, **kwargs):
        super().__init__(formats=("MDTFormat",), allowed_formats=("MDTFormat",), **kwargs)
