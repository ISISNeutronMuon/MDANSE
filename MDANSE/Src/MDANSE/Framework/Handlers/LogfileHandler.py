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

import logging.handlers

from MDANSE.Framework.Handlers.IHandler import IHandler


class LogfileHandler(IHandler, logging.handlers.RotatingFileHandler):
    """
    This class implements a logging.Handler subclass that will log messages on a rotating file. When the size of the file will exceed a given
    amount of bytes, the file is closed and a new file is opened.
    """

    def __init__(self, filename, mode="a", maxBytes=1e7, backupCount=9, delay=True):
        """
        Returns a new instance of the LogFileHandler class.

        The specified file is opened and used as the stream for logging. If mode is not specified, 'a' is used and new logging message will be appended to the file.
        If delay is true, then file  opening is deferred until the first call to emit(). By default, the file grows indefinitely.

        The maxBytes and backupCount values allows the file to rollover at a predetermined size. When the size is about to be exceeded, the file
        is closed and a new file is silently opened for output. Rollover occurs whenever the current log file is nearly maxBytes in length; if
        either of maxBytes or backupCount is zero, rollover never occurs. If backupCount is non-zero, the system will save old log files by appending
        the extensions '.1', '.2' etc., to the filename. For example, with a backupCount of 5 and a base file name of app.log, you would get app.log,
        app.log.1, app.log.2, up to app.log.5. The file being written to is always app.log. When this file is filled, it is closed and renamed to app.log.1, and if files app.log.1, app.log.2, etc. exist, then they are renamed to app.log.2, app.log.3 etc. respectively.

        :param filename: the path for the log file.
        :type filename: str
        :param mode: if 'a' the logging messages will be appended to the logfile. If 'w', at each log, the logfile will be rewritten.
        :type mode: 'a' or 'w'
        :param maxBytes: the maximum number of bytes for the logfile. When this size is exceeded, a new logfile is created.
        :type maxBytes: int
        :param backupCount: if this value is non-zero, MDANSE will save up to ``backupCount`` logfile.
        :type backupCount: int
        :param delay: if True, the logfile opening is deferred until the first call log.
        :type delay: bool
        """

        logging.handlers.RotatingFileHandler.__init__(
            self,
            filename,
            mode=mode,
            maxBytes=maxBytes,
            backupCount=backupCount,
            delay=delay,
        )
