# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/main.py
# @brief     Starts the QApplication instance
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from PyQt6.QtCore import pyqtSlot, QSize, QMetaObject, QLocale, QObject, QThread, QMutex, QSortFilterProxyModel
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QPushButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel

class Main(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """
    def __init__(self, title = "MDANSE"):
        self.setWindowTitle(title)
        