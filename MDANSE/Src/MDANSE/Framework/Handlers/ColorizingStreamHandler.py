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

import ctypes
import logging
import os

from MDANSE.Framework.Handlers.IHandler import IHandler


class ColorizingStreamHandler(IHandler, logging.StreamHandler):
    """
    This class implements a logging.Handler subclass that will log message on a terminal with a color scheme depending on the logging level.

    :copyright: 2010, 2011 Vinay Sajip
    """

    # color names to indices
    color_map = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7,
    }

    # levels to (background, foreground, bold/intense)
    if os.name == "nt":
        level_map = {
            logging.DEBUG: (None, "blue", True),
            logging.INFO: (None, "white", False),
            logging.WARNING: (None, "yellow", True),
            logging.ERROR: (None, "red", True),
            logging.CRITICAL: ("red", "white", True),
        }
    else:
        "Maps levels to colour/intensity settings."
        level_map = {
            logging.DEBUG: (None, "blue", False),
            logging.INFO: (None, "white", False),
            logging.WARNING: (None, "yellow", False),
            logging.ERROR: (None, "red", False),
            logging.CRITICAL: ("red", "white", True),
        }

    csi = "\x1b["
    reset = "\x1b[0m"

    @property
    def is_tty(self):
        """
        Returns True if the handler's stream is a terminal.

        :return: True if the handler's stream is a terminal.
        :rtype: bool
        """

        isatty = getattr(self.stream, "isatty", None)

        return isatty and isatty()

    def emit(self, record):
        """
        Log the specified logging record to this handler.

        :param record: the record to be logged.
        :type record: logging.LogRecord
        """
        try:
            message = self.format(record)
            stream = self.stream
            if str and isinstance(message, str):
                enc = getattr(stream, "encoding", "utf-8")
                message = message.encode(enc, "replace")
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, "terminator", "\n"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

    if os.name != "nt":

        def output_colorized(self, message):
            """
            Output a colorized message.

            On Linux and Mac OS X, this method just writes the
            already-colorized message to the stream, since on these
            platforms console streams accept ANSI escape sequences
            for colorization. On Windows, this handler implements a
            subset of ANSI escape sequence handling by parsing the
            message, extracting the sequences and making Win32 API
            calls to colorize the output.

            :param message: the message to colorize and output.
            :type message: str
            """

            self.stream.write(message)

    else:
        import re

        ansi_esc = re.compile(r"\x1b\[((?:\d+)(?:;(?:\d+))*)m")

        nt_color_map = {
            0: 0x00,  # black
            1: 0x04,  # red
            2: 0x02,  # green
            3: 0x06,  # yellow
            4: 0x01,  # blue
            5: 0x05,  # magenta
            6: 0x03,  # cyan
            7: 0x07,  # white
        }

        def output_colorized(self, message):
            """
            Output a colorized message.

            On Linux and Mac OS X, this method just writes the
            already-colorized message to the stream, since on these
            platforms console streams accept ANSI escape sequences
            for colorization. On Windows, this handler implements a
            subset of ANSI escape sequence handling by parsing the
            message, extracting the sequences and making Win32 API
            calls to colorize the output.

            :param message: the message to colorize and output.
            :type message: str
            """

            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, "fileno", None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2):  # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if parts:
                    params = parts.pop(0)
                    if h is not None:
                        params = [int(p) for p in params.split(";")]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08  # foreground intensity on
                            elif p == 0:  # reset to default color
                                color = 0x07
                            else:
                                pass  # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)

    def colorize(self, message, record):
        """
        Colorize a message for a logging event.

        This implementation uses the ``level_map`` class attribute to
        map the LogRecord's level to a colour/intensity setting, which is
        then applied to the whole message.

        :param message: the message to colorize.
        :type message: str
        :param record: the ``LogRecord`` for the message.
        :type record: logging.Record
        """

        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append("1")
            if params:
                message = "".join(
                    (self.csi, ";".join(params), "m", message, self.reset)
                )
        return message

    def format(self, record):
        """
        Formats a record for output.

        :param record: the logging record to be formated.
        :type record: logging.LogRecord

        :note: this implementation colorizes the message line, but leaves any traceback unolorized.
        """

        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            parts = message.split("\n", 1)
            message = "\n".join([self.colorize(p, record) for p in parts])
        return message
