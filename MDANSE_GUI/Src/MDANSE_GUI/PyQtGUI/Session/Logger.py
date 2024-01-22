import logging
import time

from qtpy.QtCore import QtMsgType
from qtpy.QtCore import QMessageLogger
from qtpy.QtCore import qInstallMessageHandler


def generate_timestamp() -> str:
    now = time.gmtime()
    timestamp = (
        "-".join([str(tx) for tx in [now.tm_mday, now.tm_mon, now.tm_year]])
        + ","
        + ":".join([str(ty) for ty in [now.tm_hour, now.tm_min, now.tm_sec]])
    )
    return timestamp


def qt_message_handler(mode, context, message):
    logger = logging.getLogger()
    details = ",".join([str(x) for x in [context.line, context.function, context.file]])
    timest = generate_timestamp
    output = ":".join([timest, details, message])
    if mode == QtMsgType.QtInfoMsg:
        logger.info(output)
    elif mode == QtMsgType.QtWarningMsg:
        logger.warning(output)
    elif mode == QtMsgType.QtCriticalMsg:
        logger.critical(output)
    elif mode == QtMsgType.QtFatalMsg:
        logger.fatal(output)
    else:
        logger.debug(output)


qInstallMessageHandler(qt_message_handler)
