#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

import time

from qtpy.QtCore import QtMsgType, qInstallMessageHandler

from MDANSE.MLogging import LOG


def generate_timestamp() -> str:
    now = time.gmtime()
    timestamp = (
        "-".join([str(tx) for tx in [now.tm_mday, now.tm_mon, now.tm_year]])
        + ","
        + ":".join([str(ty) for ty in [now.tm_hour, now.tm_min, now.tm_sec]])
    )
    return timestamp


def qt_message_handler(mode, context, message):
    details = ",".join([str(x) for x in [context.line, context.function, context.file]])
    timest = generate_timestamp
    output = ":".join([timest, details, message])
    if mode == QtMsgType.QtInfoMsg:
        LOG.info(output)
    elif mode == QtMsgType.QtWarningMsg:
        LOG.warning(output)
    elif mode == QtMsgType.QtCriticalMsg:
        LOG.critical(output)
    elif mode == QtMsgType.QtFatalMsg:
        LOG.fatal(output)
    else:
        LOG.debug(output)


qInstallMessageHandler(qt_message_handler)
