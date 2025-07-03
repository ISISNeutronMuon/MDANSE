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

import json
from collections.abc import Collection
from enum import Enum, auto
from pathlib import Path
from typing import Literal

from MDANSE.Framework.AtomMapping import check_mapping_valid, fill_remaining_labels

from .AbsConfigDesc import ConfigError, ConfigureDescriptor


class AtomMapping(ConfigureDescriptor[dict]):
    def __init__(self, default: dict[str, dict[str, str]] | str = {}, **kwargs):
        super().__init__(default=default, **kwargs)

    def validate(self, value: dict | str, file_info) -> dict:
        if isinstance(value, dict):
            pass
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except json.decoder.JSONDecodeError as err:
                raise ConfigError("Unable to load JSON string.") from err

        labels = file_info.labels
        try:
            fill_remaining_labels(value, labels)
        except AttributeError as err:
            raise ConfigError("Unable to map all atoms.") from err

        if not check_mapping_valid(value, labels):
            raise ConfigError("Atom mapping not valid.")

        return value
