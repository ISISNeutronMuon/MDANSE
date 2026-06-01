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

import logging
from enum import Enum
from typing import Any


class LogLevels(Enum):
    NONE = 0
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    NO_LOGS = NONE

    @classmethod
    def _missing_(cls, value: str) -> Any:
        if not isinstance(value, str):
            return
        value = "_".join(value.split()).upper()
        return vars(cls).get(value)


FMT = logging.Formatter(
    "%(asctime)s - %(levelname)s - process[%(process)d] - %(module)s %(lineno)d - %(message)s"
)

LOG = logging.getLogger("MDANSE")
# We need to set this to DEBUG so that when we start a multiprocessing
# job these logs get sent out to the main process. The log levels should
# be filtered at the handlers.
LOG.setLevel("DEBUG")
