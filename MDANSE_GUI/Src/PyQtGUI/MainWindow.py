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

from icecream import ic
from qtpy.QtCore import Slot, QSize, QMetaObject, QLocale, QObject, QThread, QMutex, QSortFilterProxyModel,\
                         Qt, QTimer, QPoint, Signal
from qtpy.QtGui import QFont, QAction, QEnterEvent
from qtpy.QtWidgets import QFrame,  QTabWidget, QSizePolicy, QApplication,  QMainWindow, \
                                                QToolButton,  QVBoxLayout, QWidget, \
                                                QLineEdit, QHBoxLayout, QAbstractItemView, \
                                                QFileDialog, QLabel, QToolBar, \
                                                QMenu, QWidgetAction, QTreeView

from MDANSE.PyQtGUI.BackEnd import BackEnd
from MDANSE.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE.PyQtGUI.Widgets.GeneralWidgets import ConverterDialog
from MDANSE.PyQtGUI.Resources import Resources
from MDANSE.PyQtGUI.UnitsEditor import UnitsEditor
from MDANSE.PyQtGUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE.PyQtGUI.ElementsDatabaseEditor import ElementsDatabaseEditor


class LoaderButton(QToolButton):
    """Subclassed from QToolButton, this object shows the name of a
    chemical element, and creates a pop-up menu giving access to information
    about isotopes when clicked.
    """

    load_hdf = Signal()
    start_converter = Signal(str)

    def __init__(self, *args, caption = 'Load', backend = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setText(caption)
        # self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.converter_source = backend
        
        self.clicked.connect(self.altContextMenu)
    
    # def enterEvent(self, a0: QEnterEvent) -> None:
    #     self.atom_info.emit(self.info)
    #     return super().enterEvent(a0)

    def populateMenu(self, menu: QMenu):
        hdf_action = menu.addAction("Load HDF5")
        hdf_action.triggered.connect(self.load_hdf)
        menu.addSeparator()
        for cjob in self.converter_source.backend.getConverters():
            menu.addAction("Convert using " + str(cjob))

    def altContextMenu(self):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(self.mapToGlobal(QPoint(10, 10)))
        if res is not None:
            self.start_converter.emit(res.text())

    def contextMenuEvent(self, event):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(event.globalPos())
        if res is not None:
            self.start_converter.emit(res.text())



class Main(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    file_name_for_loading = Signal(str)
    converter_name_for_dialog = Signal(str)

    def __init__(self, *args, parent = None, title = "MDANSE", settings = None,
                       **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._views = defaultdict(list)
        self._actions = []
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

    def setBackend(self, backend = None):
        """Attaches a MDANSE backend to the GUI.
        This handle is stored so we can connect
        all the QActions from the GUI
        to the correct backend slots.
        """
        self.backend = backend
        self.connectViews()
        self.attachActions()
    
    @Slot()
    def connectViews(self):
        for key in self.backend.data_holders.keys():
            skey = str(key)
            data_holder = self.backend.data_holders[skey]
            for view in self._views[skey]:
                view.setModel(data_holder)
    
    def attachActions(self):
        self.file_name_for_loading.connect(self.backend.loadFile)
        self.converter_name_for_dialog.connect(self.backend.returnConverter)
        self.loader_button.start_converter.connect(self.backend.returnConverter)
        self.backend.selected_converter.connect(self.convertTrajectory)

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
            print(f"fname[0]:{fname[0]}")
            print(f"fname[1]:{fname[1]}")
            self.file_name_for_loading.emit(fname[0])

    Slot(object)
    def convertTrajectory(self, converter = None):
        ic(f"Received converter: {converter}")
        dialog = ConverterDialog
        dialog_instance = dialog(self, converter=converter)
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        result = dialog_instance.exec()

    def setupToolbar(self):
        self._toolBar = QToolBar("Main MDANSE toolbar", self)
        # self._toolBar.setMovable(True)
        self._toolBar.setObjectName("main toolbar")
        loader = LoaderButton(backend = self)
        loader.setIcon(self.resources._icons['plus'])
        loader.load_hdf.connect(self.loadTrajectory)
        self.loader_button = loader
        self._toolBar.addWidget(loader)
        valid_keys = [
            # ('load', self.loadTrajectory),
            # ('plus', self.loadTrajectory),
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

