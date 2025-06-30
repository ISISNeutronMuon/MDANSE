import logging
from enum import Enum


class LogLevels(Enum):
    NONE = 0
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    NO_LOGS = NONE

    @classmethod
    def _missing_(cls, value: str):
        if not isinstance(value, str):
            return

        value = "_".join(value.split()).upper()

        for member in cls.members:
            if value == member.name:
                return member

FMT = logging.Formatter(
    "%(asctime)s - %(levelname)s - process[%(process)d] - %(module)s %(lineno)d - %(message)s"
)

LOG = logging.getLogger("MDANSE")
# We need to set this to DEBUG so that when we start a multiprocessing
# job these logs get sent out to the main process. The log levels should
# be filtered at the handlers.
LOG.setLevel("DEBUG")
