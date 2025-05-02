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
import re
from collections.abc import Container
from enum import Enum
from math import isclose
from typing import Optional, Set, SupportsFloat

from .AbsConfigDesc import ConfigError, ConfigureDescriptor


class Cases(Enum):
    PRESERVE = lambda x: x
    UPPER = str.upper
    LOWER = str.lower
    TITLE = str.title

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()

        for member in cls:
            if member.name == value or member.value is value:
                return member
        return NotImplemented


class StringConfigDesc(ConfigureDescriptor[str]):
    """
    This configurator allows to input a string value.
    """

    def __init__(
            self,
            *,
            case: Cases = Cases.PRESERVE,
            choices: Container[str] = None,
            regex: re.Pattern = None,
            **params,
    ):
        super().__init__(**params)
        self.case = Cases(case)
        self.choices = choices
        self.regex = re.compile(regex)


    def validate(self, value: str, *_) -> float:
        try:
            value = str(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid str.") from error

        value = self.case.value(value)

        super().validate(value)

        if not self.regex.match(value):
            raise ConfigError(f"Value ({value}) does not match requirement {self.regex.pattern}.")

        return value
