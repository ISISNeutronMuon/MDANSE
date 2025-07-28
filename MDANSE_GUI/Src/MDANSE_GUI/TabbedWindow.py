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
from __future__ import annotations

import os
from collections import defaultdict
from importlib import metadata
from pathlib import PurePath

from qtpy.QtCore import QMessageLogger, QSize, Qt, QTimer, QUrl, Signal, Slot
from qtpy.QtGui import QDesktopServices
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QToolBar,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE_GUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE_GUI.Resources import Resources
from MDANSE_GUI.Session.StructuredSession import StructuredSession
from MDANSE_GUI.Tabs.ConverterTab import ConverterTab
from MDANSE_GUI.Tabs.InstrumentTab import InstrumentTab
from MDANSE_GUI.Tabs.JobTab import JobTab
from MDANSE_GUI.Tabs.LoggingTab import GuiLogHandler, LoggingTab
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.Models.TrajectoryModel import TrajectoryModel
from MDANSE_GUI.Tabs.PlotSelectionTab import PlotSelectionTab
from MDANSE_GUI.Tabs.PlotTab import PlotTab
from MDANSE_GUI.Tabs.RunTab import RunTab
from MDANSE_GUI.Tabs.TrajectoryTab import TrajectoryTab
from MDANSE_GUI.Tabs.Views.PlotDataView import PlotDataView
from MDANSE_GUI.UnitsEditor import UnitsEditor
from MDANSE_GUI.UserSettingsEditor import UserSettingsEditor
from MDANSE_GUI.Widgets.NotificationTabWidget import NotificationTabWidget
from MDANSE_GUI.Widgets.StyleDialog import StyleDatabase, StyleDialog

MDANSE_CODE_WEBSITE = QUrl("https://github.com/ISISNeutronMuon/MDANSE")
MDANSE_DOCS_WEBSITE = QUrl("https://mdanse.readthedocs.io/en/latest/")
MDANSE_PROJECT_WEBSITE = QUrl("https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx")


class TabbedWindow(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    def __init__(
        self,
        *args,
        parent=None,
        title="MDANSE",
        settings=None,
        app_instance=None,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.tabs = NotificationTabWidget(self)
        self.setCentralWidget(self.tabs)
        self._views = defaultdict(list)
        self._actions = []
        self._tabs = {}
        self._session = StructuredSession()
        self._settings = self._session.obtain_settings(self)
        self._logger = QMessageLogger()
        self._toolbar_buttons = []  # list of (widget, icon_key:str) pairs
        self._style_database = StyleDatabase(self)
        self.setWindowTitle(title)
        self.resources = Resources()
        self.current_object = None
        self.startSettings(settings)
        self.createCommonModels()
        self.makeBasicLayout()
        self.workdir = os.path.expanduser("~")

        self.periodic_table = PeriodicTableViewer(self)
        self.element_editor = ElementsDatabaseEditor(self)
        self.unit_editor = UnitsEditor(self)
        self.style_selector = StyleDialog(self)
        self.style_selector.connectStyleDatabase(self._style_database)
        self.style_selector.new_style.connect(self.setStyleSheet)
        self.style_selector.icon_swap.connect(self.invertToolbar)

        if app_instance is not None:
            app_instance.aboutToQuit.connect(self._session.save)
        self._session.load()
        self.settings_editor = UserSettingsEditor(self, current_session=self._session)

        self._tabs["Plot Creator"]._visualiser.data_for_plotting.connect(
            self._tabs["Plot Holder"].accept_external_data
        )
        self._tabs["Plot Creator"]._visualiser.create_new_plot.connect(
            self._tabs["Plot Holder"]._visualiser.new_plot
        )
        self._tabs["Plot Creator"]._visualiser.create_new_text.connect(
            self._tabs["Plot Holder"]._visualiser.new_text
        )
        self._tabs["Instruments"]._visualiser.instrument_details_changed.connect(
            self._tabs["Actions"].update_action_after_instrument_change
        )

        self.tabs.currentChanged.connect(self.tabs.reset_current_color)
        self.check_dark_mode()

    def check_dark_mode(self):
        style_hints = QApplication.styleHints()
        colour_scheme = style_hints.colorScheme()
        if colour_scheme == Qt.ColorScheme.Dark:
            self.invertToolbar(dark=True)
        else:
            self.invertToolbar(dark=False)

    def createCommonModels(self):
        self._trajectory_model = TrajectoryModel()
        self._instrument_model = GeneralModel()
        self._job_holder = JobHolder()
        self._gui_log_handler = GuiLogHandler()

    def makeBasicLayout(self):
        self.createConverterViewer()
        self.createTrajectoryViewer()
        self.createActionsViewer()
        self.createJobsViewer()
        self.createPlotSelection()
        self.createPlotHolder()
        self.createInstrumentSelector()
        self.createLogViewer()
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
        settings_group = menubar.addMenu("Settings")
        help_group = menubar.addMenu("Help")
        self.exitAct = QAction("Exit", parent=menubar)
        self.exitAct.triggered.connect(self.shut_down)
        file_group.addAction(self.exitAct)
        self.settingsAct = QAction("User Settings", parent=menubar)
        self.settingsAct.triggered.connect(self.launchSettingsEditor)
        settings_group.addAction(self.settingsAct)
        self.aboutAct = QAction("About MDANSE", parent=menubar)
        self.aboutAct.triggered.connect(self.version_information)
        self.website_actions = []
        for label, function in [
            ("project", self.show_website_project),
            ("source code", self.show_website_code),
            ("documentation", self.show_website_docs),
        ]:
            temp_action = QAction(f"Open MDANSE {label} website", parent=menubar)
            temp_action.triggered.connect(function)
            self.website_actions.append(temp_action)
        help_group.addActions(self.website_actions)
        help_group.addSeparator()
        help_group.addAction(self.aboutAct)
        self.setMenuBar(menubar)

    def shut_down(self):
        QApplication.quit()
        self.destroy(True, True)

    def version_information(self):
        version = ""
        version += f"MDANSE version: {metadata.version('MDANSE')}\n"
        version += f"MDANSE_GUI version: {metadata.version('MDANSE_GUI')}\n"
        _popup = QMessageBox.about(self, "MDANSE Version Information", version)

    def show_website_code(self):
        QDesktopServices.openUrl(MDANSE_CODE_WEBSITE)

    def show_website_project(self):
        QDesktopServices.openUrl(MDANSE_PROJECT_WEBSITE)

    def show_website_docs(self):
        QDesktopServices.openUrl(MDANSE_DOCS_WEBSITE)

    def setupToolbar(self):
        self._toolBar = QToolBar("Main MDANSE toolbar", self)
        # self._toolBar.setMovable(True)
        self._toolBar.setObjectName("main toolbar")
        self._toolBar.setIconSize(QSize(32, 32))
        self._toolBar.setMovable(False)
        self._toolBar.setMinimumHeight(24)
        self._toolBar.setMaximumHeight(80)
        valid_keys = [
            ("periodic_table", self.launchPeriodicTable),
            ("element", self.launchElementsEditor),
            ("units", self.launchUnitsEditor),
            ("user_definitions", self.launchStyleSelector),
        ]
        tooltips = {
            "periodic_table": "Periodic Table of Elements",
            "element": "Atom Property Editor",
            "units": "Physical Units defintions",
            "user_definitions": "Customise GUI Style",
        }
        for key, slot in valid_keys:
            icon = self.resources._icons[key]
            action = QAction(icon, str(key), self._toolBar)
            action.triggered.connect(slot)
            action.setToolTip(tooltips[key])
            self._actions.append(action)
            self._toolbar_buttons.append((action, key))
            # self._actions.append(self._toolBar.addAction(icon, str(key)))
        for act in self._actions:
            self._toolBar.addAction(act)
        self.addToolBar(self._toolBar)
        LOG.info(f"Icon size is {self._toolBar.iconSize()}")

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
    def launchSettingsEditor(self):
        self.settings_editor.update_combo()
        self.launch_dialog(self.settings_editor)

    @Slot()
    def launchElementsEditor(self):
        self.launch_dialog(self.element_editor)

    def launch_dialog(self, dialog) -> None:
        if dialog.isVisible():
            geometry = dialog.saveGeometry()
            dialog.previous_geometry = geometry
            dialog.close()
        else:
            if hasattr(dialog, "previous_geometry"):
                dialog.restoreGeometry(dialog.previous_geometry)
            dialog.show()

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
        self._job_holder.trajectory_for_loading.connect(trajectory_tab.load_trajectory)
        self._job_holder.trajectory_for_loading.connect(trajectory_tab.tab_notification)

    def createInstrumentSelector(self):
        name = "Instruments"
        instrument_tab = InstrumentTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            model=self._instrument_model,
        )
        self.tabs.addTab(instrument_tab._core, name)
        self._tabs[name] = instrument_tab

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
        self.tabs.tabBar().tabBarClicked.connect(
            job_tab.update_action_on_tab_activation
        )

    def createActionsViewer(self):
        name = "Actions"
        job_tab = JobTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
            combo_model=self._trajectory_model,
            instrument_model=self._instrument_model,
        )
        job_tab.set_job_starter(self._job_holder)
        jobtab_index = self.tabs.addTab(job_tab._core, name)
        job_tab.set_own_index(jobtab_index)
        self._tabs[name] = job_tab
        self.tabs.tabBar().tabBarClicked.connect(
            job_tab.update_action_on_tab_activation
        )

    def createPlotSelection(self):
        name = "Plot Creator"
        plot_tab = PlotSelectionTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
        )
        self.tabs.addTab(plot_tab._core, name)
        self._tabs[name] = plot_tab
        self._job_holder.results_for_loading.connect(plot_tab.load_results)
        self._job_holder.results_for_loading.connect(plot_tab.tab_notification)
        plot_tab._view.fast_plotting_data.connect(self.accept_external_data)

    def accept_external_data(self, model):
        self._tabs["Plot Creator"]._visualiser.new_plot()
        self._tabs["Plot Holder"].accept_external_data(model)

    def createPlotHolder(self):
        name = "Plot Holder"
        plot_tab = PlotTab.gui_instance(
            self.tabs,
            name,
            self._session,
            self._settings,
            self._logger,
        )
        plot_tab.connect_units()
        self.tabs.addTab(plot_tab._core, name)
        self._tabs[name] = plot_tab

    def createLogViewer(self):
        name = "Logger"
        LOG.addHandler(self._gui_log_handler)
        log_tab = LoggingTab.gui_instance(
            self.tabs, name, self._session, self._settings, self._logger
        )
        log_tab.add_handler(self._gui_log_handler)
        self.tabs.addTab(log_tab._core, name)
        self._tabs[name] = log_tab

    @Slot()
    def saveSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

    def reportError(self, text: str):
        LOG.error(text)
