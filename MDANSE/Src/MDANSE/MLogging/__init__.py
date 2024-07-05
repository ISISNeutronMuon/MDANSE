import logging

FMT = logging.Formatter(
    "%(asctime)s - %(levelname)s - process[%(process)d] - %(module)s %(lineno)d - %(message)s"
)

LOG = logging.getLogger("MDANSE")
LOG.setLevel("INFO")
