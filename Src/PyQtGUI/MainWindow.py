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

import os
from collections import defaultdict

from qtpy.QtCore import Slot, QSize, QMetaObject, QLocale, QObject, QThread, QMutex, QSortFilterProxyModel,\
                         Qt, QTimer, QDir, Signal
from qtpy.QtGui import QFont, QAction
from qtpy.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QPushButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel, QToolBar, \
                                                QMenuBar, QWidgetAction, QTreeView

from MDANSE.PyQtGUI.BackEnd import BackEnd
from MDANSE.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE.PyQtGUI.FrontEnd import FrontEnd
from MDANSE.PyQtGUI.Resources import Resources
from MDANSE.PyQtGUI.UnitsEditor import UnitsEditor
from MDANSE.PyQtGUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE.PyQtGUI.ElementsDatabaseEditor import ElementsDatabaseEditor


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
        self.workdir = os.path.expanduser('~')
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

    Slot()
    def launchPeriodicTable(self):
        dialog = PeriodicTableViewer
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    Slot()
    def launchUnitsEditor(self):
        dialog = UnitsEditor
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    Slot()
    def launchElementsEditor(self):
        dialog = ElementsDatabaseEditor
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    Slot()
    def loadTrajectory(self):
        fname = QFileDialog.getOpenFileName(self, "Load an MD trajectory",
                                    self.workdir, 'HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)')
        if fname is not None:
            self.file_name_for_loading.emit(fname)

    def setupToolbar(self):
        self._toolBar = QToolBar("Main MDANSE toolbar", self)
        # self._toolBar.setMovable(True)
        self._toolBar.setObjectName("main toolbar")
        valid_keys = [
            ('plus', self.loadTrajectory),
            ('periodic_table', self.launchPeriodicTable),
            ('element', self.launchElementsEditor),
            ('units', self.launchUnitsEditor),
        ]
        for key, slot in valid_keys:
            icon = self.resources._icons[key]
            action = QAction(icon, str(key), self._toolBar)
            action.triggered.connect(slot)
            self._actions.append(action)
            # self._actions.append(self._toolBar.addAction(icon, str(key)))
        for act in self._actions:
            self._toolBar.addAction(act)
        self.addToolBar(self._toolBar)
        print(f"Icon size is {self._toolBar.iconSize()}")

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

    @Slot()
    def saveSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

    def onMyToolBarButtonClick(self, s):
        print("click", s)

