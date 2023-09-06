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
