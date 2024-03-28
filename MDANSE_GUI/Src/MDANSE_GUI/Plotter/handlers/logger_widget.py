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


class LoggerWidget(QtWidgets.QPlainTextEdit, logging.Handler):
    def __init__(self, parent):
        super(LoggerWidget, self).__init__()
        self.setReadOnly(True)

    def close(self):
        """Close the handler."""
        logging.Handler.close(self)

    def emit(self, record):
        """Emit the message.

        Args:
            record (logging.LogRecord): the log record
        """
        msg = self.format(record)
        self.appendPlainText(msg)

    def contextMenuEvent(self, event):
        """Opens a contextual menu.

        Args:
            event (qtpy.QtCore.QEvent): the event
        """
        popup_menu = self.createStandardContextMenu()

        popup_menu.addSeparator()
        popup_menu.addAction("Clear", self.on_clear_logger)
        popup_menu.addSeparator()
        popup_menu.addAction("Save as ...", self.on_save_logger)
        popup_menu.exec_(event.globalPos())

    def on_clear_logger(self):
        """Clear the logger"""
        self.clear()

    def on_save_logger(self):
        """Save the logger contents to a file"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File")
        if not filename:
            return

        with open(filename, "w") as fin:
            fin.write(self.toPlainText())
