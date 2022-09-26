# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/MainWindow.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from PyQt6.QtCore import pyqtSlot, QSize, QMetaObject, QLocale, QObject, QThread, QMutex, QSortFilterProxyModel
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QPushButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel, \
                                                QMenuBar, QWidgetAction


class Main(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    def __init__(self, parent = None, title = "MDANSE"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.makeBasicLayout()

    def setBackend(self, backend = None):
        """Attaches a MDANSE backend to the GUI.
        This handle is stored so we can connect
        all the QActions from the GUI
        to the correct backend slots.
        """
        self.backend = backend

    def makeBasicLayout(self):
        self.menuBar = QMenuBar(self)
    
    def attachActions(self):
        QAction(parent=self)

