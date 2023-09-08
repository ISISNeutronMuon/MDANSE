# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     root file of pygenplot
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

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
