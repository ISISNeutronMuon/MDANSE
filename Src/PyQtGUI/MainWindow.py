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
                         Qt, QTimer, QDir
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QPushButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel, QToolBar, \
                                                QMenuBar, QWidgetAction, QTreeView

from MDANSE.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE.PyQtGUI.FrontEnd import FrontEnd
from MDANSE.PyQtGUI.Resources import Resources

class Main(QMainWindow, FrontEnd):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    def __init__(self, parent = None, title = "MDANSE", settings = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.wid_gen = WidgetGenerator()
        self.resources = Resources()
        self.makeBasicLayout()
        self.settings = settings
        if settings is not None:
            settings.beginGroup("MainWindow")
            geo = settings.value("geometry")
            if geo:
                self.restoreGeometry(geo)
            state = settings.value("state")
            if state:
                self.restoreState(state)
            settings.endGroup()
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.saveSettings)
        self.settings_timer.setInterval(2000)
        self.settings_timer.start()
        self.destroyed.connect(self.settings_timer.stop)

    def makeBasicLayout(self):
        self.createTrajectoryViewer()
        self.createJobsViewer()
        self.setupMenubar()
        self.setupToolbar()
    
    def setupMenubar(self):
        self._menuBar = self.menuBar()
        self._menuBar.setObjectName("main menubar")
        self._menuBar.setVisible(True)
        self.exitAct = QAction("Exit", parent = self._menuBar)
        self.exitAct.triggered.connect(self.destroy)
        self._menuBar.addAction(self.exitAct)

    def setupToolbar(self):
        self._toolBar = QToolBar(self)
        self._toolBar.setMovable(True)
        self._toolBar.setObjectName("main toolbar")
        self.addToolBar(self._toolBar)
        for key, icon in self.resources._icons.items():
            # action = QAction(icon, str(key), self._toolBar)
            # self._actions.append(action)
            self._toolBar.addAction(icon, str(key))
        for act in self._actions:
            self._toolBar.addAction(act)

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

    @pyqtSlot()
    def saveSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

