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
from qtpy.QtCore import (
    Slot,
    Qt,
    QTimer,
    Signal,
    QMessageLogger,
)
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QMainWindow, QFileDialog, QToolBar, QTreeView, QTabWidget

from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Settings.LocalSettings import LocalSettings
from MDANSE_GUI.Widgets.Generator import WidgetGenerator
from MDANSE_GUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.Resources import Resources
from MDANSE_GUI.UnitsEditor import UnitsEditor
from MDANSE_GUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE_GUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.TrajectoryTab import TrajectoryTab
from MDANSE_GUI.Tabs.JobTab import JobTab
from MDANSE_GUI.Tabs.MolecularViewerTab import MolecularViewerTab
from MDANSE_GUI.Tabs.RunTab import RunTab
from MDANSE_GUI.Tabs.LoggingTab import LoggingTab
from MDANSE_GUI.Tabs.ConverterTab import ConverterTab
from MDANSE_GUI.Widgets.StyleDialog import StyleDialog, StyleDatabase
from MDANSE_GUI.Plotter.widgets.main_window import MainWindow


class TabbedWindow(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    file_name_for_loading = Signal(str)
    converter_name_for_dialog = Signal(str)

    def __init__(self, *args, parent=None, title="MDANSE", settings=None, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        self._views = defaultdict(list)
        self._actions = []
        self._tabs = {}
        self._settings = LocalSettings()
        self._session = LocalSession()
        self._logger = QMessageLogger()
        self._toolbar_buttons = []  # list of (widget, icon_key:str) pairs
        self._style_database = StyleDatabase(self)
        self.setWindowTitle(title)
        self.wid_gen = WidgetGenerator()
        self.resources = Resources()
        self.current_object = None
        self.startSettings(settings)
        self.createCommonModels()
        self.makeBasicLayout()
        self.workdir = os.path.expanduser("~")

    def createCommonModels(self):
        self._trajectory_model = GeneralModel()
        self._job_holder = JobHolder()

    def makeBasicLayout(self):
        self.createConverterViewer()
        self.createTrajectoryViewer()
        self.createMolecularViewer()
        self.createActionsViewer()
        self.createJobsViewer()
        # self.createLogViewer()
        self.setupMenubar()
        self.setupToolbar()

    def startSettings(self, init_settings):
        self.settings = init_settings
        if self.settings is not None:
            self.settings.beginGroup("MainWindow")
            geo = self.settings.value("geometry")
            if geo:
                self.restoreGeometry(geo)
            state = self.settings.value("state")
            if state:
                self.restoreState(state)
            self.settings.endGroup()
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.saveSettings)
        self.settings_timer.setInterval(2000)
        self.settings_timer.start()
        self.destroyed.connect(self.settings_timer.stop)

    def setupMenubar(self):
        self._menuBar = self.menuBar()
        self._menuBar.setObjectName("main menubar")
        self._menuBar.setVisible(True)
        self.exitAct = QAction("Exit", parent=self._menuBar)
        self.exitAct.triggered.connect(self.destroy)
        self._menuBar.addAction(self.exitAct)

    def setupToolbar(self):
        self._toolBar = QToolBar("Main MDANSE toolbar", self)
        # self._toolBar.setMovable(True)
        self._toolBar.setObjectName("main toolbar")
        valid_keys = [
            # ('load', self.loadTrajectory),
            # ('plus', self.loadTrajectory),
            ("plot", self.launchDataPlotter),
            ("periodic_table", self.launchPeriodicTable),
            ("element", self.launchElementsEditor),
            ("units", self.launchUnitsEditor),
            ("user", self.launchStyleSelector),
        ]
        for key, slot in valid_keys:
            icon = self.resources._icons[key]
            action = QAction(icon, str(key), self._toolBar)
            action.triggered.connect(slot)
            self._actions.append(action)
            self._toolbar_buttons.append((action, key))
            # self._actions.append(self._toolBar.addAction(icon, str(key)))
        for act in self._actions:
            self._toolBar.addAction(act)
        self.addToolBar(self._toolBar)
        print(f"Icon size is {self._toolBar.iconSize()}")

    @Slot()
    def launchPeriodicTable(self):
        dialog = PeriodicTableViewer
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    @Slot()
    def launchUnitsEditor(self):
        dialog = UnitsEditor
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    @Slot()
    def launchStyleSelector(self):
        dialog = StyleDialog
        dialog_instance = dialog(self)
        dialog_instance.connectStyleDatabase(self._style_database)
        dialog_instance.show()
        dialog_instance.new_style.connect(self.setStyleSheet)
        dialog_instance.icon_swap.connect(self.invertToolbar)
        result = dialog_instance.exec()

    @Slot()
    def launchElementsEditor(self):
        dialog = ElementsDatabaseEditor
        dialog_instance = dialog(self)
        dialog_instance.show()
        result = dialog_instance.exec()

    @Slot()
    def launchDataPlotter(self):
        dialog = MainWindow
        dialog_instance = dialog(self)
        dialog_instance.show()

    @Slot()
    def loadTrajectory(self):
        fname = QFileDialog.getOpenFileName(
            self,
            "Load an MD trajectory",
            self.workdir,
            "MDT files (*.mdt);;HDF5 files (*.h5 *.hdf);;All files(*.*)",
        )
        ic(fname)
        if len(fname[0]) > 0:
            self.file_name_for_loading.emit(fname[0])

    @Slot(object)
    def convertTrajectory(self, converter=None):
        ic(f"Received converter: {converter}")
        dialog = ActionDialog
        try:
            dialog_instance = dialog(self, converter=converter)
        except:
            self.reportError(
                f"Failed to create the dialog: {dialog} for converter {converter}"
            )
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        try:
            result = dialog_instance.exec()
        except:
            self.reportError(
                f"Dialog execution failed in dialog: {dialog} for converter {converter}"
            )

    @Slot(object)
    def runAction(self, converter=None):
        ic(f"Received action: {converter}")
        dialog = ActionDialog
        try:
            dialog_instance = dialog(
                self, converter=converter, source_object=self.current_object
            )
        except:
            self.reportError(
                f"Failed to create the dialog: {dialog} for action {converter}"
            )
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        try:
            result = dialog_instance.exec()
        except:
            self.reportError(
                f"Dialog execution failed in dialog: {dialog} for action {converter}"
            )

    @Slot(bool)
    def invertToolbar(self, dark=False):
        if dark:
            for obj, key in self._toolbar_buttons:
                obj.setIcon(self.resources._inverted_icons[key])
        else:
            for obj, key in self._toolbar_buttons:
                obj.setIcon(self.resources._icons[key])

    def createTrajectoryViewer(self):
        name = "Trajectories"
        trajectory_tab = TrajectoryTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            model=self._trajectory_model,
        )
        self.tabs.addTab(trajectory_tab._core, name)
        self._tabs[name] = trajectory_tab

    def createMolecularViewer(self):
        name = "3D View"
        molview_tab = MolecularViewerTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            model=self._trajectory_model,
        )
        self.tabs.addTab(molview_tab._core, name)
        self._tabs[name] = molview_tab

    def createJobsViewer(self):
        name = "Running Jobs"
        run_tab = RunTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            model=self._job_holder,
        )
        self.tabs.addTab(run_tab._core, name)
        self._tabs[name] = run_tab

    def createConverterViewer(self):
        name = "Converters"
        job_tab = ConverterTab.gui_instance(
            self.tabs, name, self._session, self._settings, self._logger
        )
        job_tab.set_job_starter(self._job_holder)
        self.tabs.addTab(job_tab._core, name)
        self._tabs[name] = job_tab

    def createActionsViewer(self):
        name = "Actions"
        job_tab = JobTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            combo_model=self._trajectory_model,
        )
        job_tab.set_job_starter(self._job_holder)
        self.tabs.addTab(job_tab._core, name)
        self._tabs[name] = job_tab

    def createLogViewer(self):
        name = "Logger"
        log_tab = LoggingTab.gui_instance(
            self.tabs, name, self._session, self._settings, self._logger
        )
        self.tabs.addTab(log_tab._core, name)
        self._tabs[name] = log_tab

    @Slot()
    def saveSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

    def reportError(self, text: str):
        print(text)
