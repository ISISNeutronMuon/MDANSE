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
