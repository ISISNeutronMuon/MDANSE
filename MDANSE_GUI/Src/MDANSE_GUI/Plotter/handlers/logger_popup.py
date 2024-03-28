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

import logging

from qtpy import QtWidgets


class LoggerPopup(logging.Handler):
    def emit(self, record):
        """Emit the message.

        Args:
            record (logging.LogRecord): the log record
        """
        msg = self.format(record)
        message_box = QtWidgets.QMessageBox()
        message_box.setText(msg)
        message_box.setWindowTitle("Message")
        message_box.exec()
