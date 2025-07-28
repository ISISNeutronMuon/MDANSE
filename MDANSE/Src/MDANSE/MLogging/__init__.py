from __future__ import annotations

import logging

FMT = logging.Formatter(
    "%(asctime)s - %(levelname)s - process[%(process)d] - %(module)s %(lineno)d - %(message)s"
)

LOG = logging.getLogger("MDANSE")
# We need to set this to DEBUG so that when we start a multiprocessing
# job these logs get sent out to the main process. The log levels should
# be filtered at the handlers.
LOG.setLevel("DEBUG")
