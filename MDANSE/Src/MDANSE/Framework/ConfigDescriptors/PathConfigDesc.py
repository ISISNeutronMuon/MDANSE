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
from pathlib import Path
from typing import Collection, Literal
from enum import Enum, auto

from .AbsConfigDesc import ConfigError, ConfigureDescriptor

class Modes(Enum):
    MUST_EXIST = auto()
    MAY_EXIST = auto()
    MUST_NOT_EXIST = auto()

    R = MUST_EXIST
    W = MAY_EXIST
    X = MUST_NOT_EXIST
    A = MUST_EXIST


class PathConfigDesc(ConfigureDescriptor[Path]):
    """
    This configurator allows to input a path value.
    """
    def __init__(
            self,
            mode: Modes,
            *,
            extensions: Collection[str] = (),
            directory: bool = False,
            **params,
    ):
        super().__init__(**params)

        self.mode = Modes[mode.upper()] if isinstance(mode, str) else Modes(mode)

        self.extension = extensions
        self.directory = directory

    def validate(self, value, *_) -> Path:
        try:
            value = Path(value)
        except Exception as error:
            raise ConfigError(f"Value ({value}) is not a valid Path.") from error

        super().validate(value)

        if self.mode is Modes.MAY_EXIST:
            pass
        elif self.mode is Modes.MUST_EXIST and not value.exists():
            raise ConfigError(f"File at ({value}) does not exist.")
        elif self.mode is Modes.MUST_NOT_EXIST and value.exists():
            raise ConfigError(f"File at ({value}) must not exist.")

        return value
