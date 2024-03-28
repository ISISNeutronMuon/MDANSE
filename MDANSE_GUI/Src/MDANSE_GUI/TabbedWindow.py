#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
from collections import defaultdict
from importlib import metadata

from icecream import ic
from qtpy.QtCore import Slot, QTimer, Signal, QMessageLogger, Qt
from qtpy.QtGui import QAction
from qtpy.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QToolBar,
    QTabWidget,
    QMenuBar,
    QMessageBox,
    QApplication,
)

import MDANSE

from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Settings.LocalSettings import LocalSettings
from MDANSE_GUI.Widgets.Generator import WidgetGenerator
from MDANSE_GUI.Resources import Resources
from MDANSE_GUI.UnitsEditor import UnitsEditor
from MDANSE_GUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE_GUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.TrajectoryTab import TrajectoryTab
from MDANSE_GUI.Tabs.JobTab import JobTab
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

        self.data_plotter = MainWindow(self)
        self.periodic_table = PeriodicTableViewer(self)
        self.element_editor = ElementsDatabaseEditor(self)
        self.unit_editor = UnitsEditor(self)
        self.style_selector = StyleDialog(self)
        self.style_selector.connectStyleDatabase(self._style_database)
        self.style_selector.new_style.connect(self.setStyleSheet)
        self.style_selector.icon_swap.connect(self.invertToolbar)

    def createCommonModels(self):
        self._trajectory_model = GeneralModel()
        self._job_holder = JobHolder()

    def makeBasicLayout(self):
        self.createConverterViewer()
        self.createTrajectoryViewer()
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
        menubar = QMenuBar()
        menubar.setNativeMenuBar(False)  # this works around PyQt problems on MacOS
        menubar.setObjectName("main menubar")
        menubar.setVisible(True)
        file_group = menubar.addMenu("File")
        help_group = menubar.addMenu("Help")
        self.exitAct = QAction("Exit", parent=menubar)
        self.exitAct.triggered.connect(self.shut_down)
        file_group.addAction(self.exitAct)
        self.aboutAct = QAction("About MDANSE", parent=menubar)
        self.aboutAct.triggered.connect(self.version_information)
        help_group.addAction(self.aboutAct)
        self.setMenuBar(menubar)

    def shut_down(self):
        QApplication.quit()
        self.destroy(True, True)

    def version_information(self):
        version = ""
        version += f"MDANSE version: {metadata.version('MDANSE')}\n"
        version += f"MDANSE_GUI version: {metadata.version('MDANSE_GUI')}\n"
        popup = QMessageBox.about(self, "MDANSE Version Information", version)

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
        self.launch_dialog(self.periodic_table)

    @Slot()
    def launchUnitsEditor(self):
        self.launch_dialog(self.unit_editor)

    @Slot()
    def launchStyleSelector(self):
        self.launch_dialog(self.style_selector)

    @Slot()
    def launchElementsEditor(self):
        self.launch_dialog(self.element_editor)

    @Slot()
    def launchDataPlotter(self):
        self.launch_dialog(self.data_plotter)

    def launch_dialog(self, dialog) -> None:
        if dialog.isVisible():
            if dialog.isMaximized():
                dialog.showMaximized()
            else:
                dialog.showNormal()
            dialog.activateWindow()
        else:
            dialog.show()

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
