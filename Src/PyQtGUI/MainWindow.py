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

from collections import defaultdict

from PyQt6.QtCore import pyqtSlot, QSize, QMetaObject, QLocale, QObject, QThread, QMutex, QSortFilterProxyModel,\
                         Qt
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QPushButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel, \
                                                QMenuBar, QWidgetAction, QTreeView

from MDANSE.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE.PyQtGUI.FrontEnd import FrontEnd

class Main(QMainWindow, FrontEnd):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    def __init__(self, parent = None, title = "MDANSE"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.wid_gen = WidgetGenerator()
        self.makeBasicLayout()

    def makeBasicLayout(self):
        self.menuBar = QMenuBar(self)
        self.exitAct = QAction("Exit", parent = self.menuBar)
        self.exitAct.triggered.connect(self.destroy)
        self.menuBar.addAction(self.exitAct)
        self.createTrajectoryViewer()
        self.createJobsViewer()

    def createTrajectoryViewer(self):
        base, temp = self.wid_gen.wrapWidget(cls = QTreeView, parent= self, dockable = True,
                                             name="Trajectories")
        self.traj_view = temp
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, base)
        self._views['trajectory'].append(temp)

    def createJobsViewer(self):
        base, temp = self.wid_gen.wrapWidget(cls = QTreeView, parent= self, dockable = True,
                                             name="Jobs")
        self.job_view = temp
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, base)
        self._views['jobs'].append(temp)


