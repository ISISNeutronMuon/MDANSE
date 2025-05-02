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
import json

from .AbsConfigDesc import ConfigError, ConfigureDescriptor

class AtomMapping(ConfigureDescriptor[dict]):
    def __init__(self, default: dict | str = {}, **kwargs):
        super().__init__(**kwargs)


    def validate(self, value: dict | str, *_) -> dict:
        if isinstance(value, dict):
            ...
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except json.decoder.JSONDecodeError as err:
                raise ConfigError("Unable to load JSON string.") from err
