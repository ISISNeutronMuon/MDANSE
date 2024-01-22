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
)
from qtpy.QtGui import QAction
from qtpy.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QToolBar,
    QTreeView,
)

from MDANSE_GUI.PyQtGUI.DataViewModel.TrajectoryHolder import DataTreeItem
from MDANSE_GUI.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE_GUI.PyQtGUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.PyQtGUI.Tabs.Views.ActionsTree import ActionsTree
from MDANSE_GUI.PyQtGUI.Widgets.LoaderButton import LoaderButton
from MDANSE_GUI.PyQtGUI.Resources import Resources
from MDANSE_GUI.PyQtGUI.UnitsEditor import UnitsEditor
from MDANSE_GUI.PyQtGUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE_GUI.PyQtGUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE_GUI.PyQtGUI.Widgets.TrajectoryViewer import TrajectoryViewer
from MDANSE_GUI.PyQtGUI.MolecularViewer.MolecularViewer import MolecularViewer
from MDANSE_GUI.PyQtGUI.MolecularViewer.Controls import ViewerControls
from MDANSE_GUI.PyQtGUI.Widgets.StyleDialog import StyleDialog, StyleDatabase
from MDANSE_GUI.PyQtGUI.Plotter.widgets.main_window import MainWindow


class MainWindow(QMainWindow):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    file_name_for_loading = Signal(str)
    converter_name_for_dialog = Signal(str)

    def __init__(self, *args, parent=None, title="MDANSE", settings=None, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._views = defaultdict(list)
        self._actions = []
        self._toolbar_buttons = []  # list of (widget, icon_key:str) pairs
        self._style_database = StyleDatabase(self)
        self.setWindowTitle(title)
        self.wid_gen = WidgetGenerator()
        self.resources = Resources()
        self.current_object = None
        self.startSettings(settings)
        self.makeBasicLayout()
        self.workdir = os.path.expanduser("~")

    def makeBasicLayout(self):
        self.createTrajectoryViewer()
        self.createJobsViewer()
        self.createActionsViewer()
        self.setupMenubar()
        self.setupToolbar()
        self.createMolecularViewer()

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

    def setBackend(self, backend=None):
        """Attaches a MDANSE backend to the GUI.
        This handle is stored so we can connect
        all the QActions from the GUI
        to the correct backend slots.
        """
        self.backend = backend
        self.connectViews()
        self.attachActions()
        self.backend.new_trajectory.connect(self._visualiser._new_trajectory)

    @Slot()
    def connectViews(self):
        for key in self.backend.data_holders.keys():
            skey = str(key)
            data_holder = self.backend.data_holders[skey]
            for view in self._views[skey]:
                view.setModel(data_holder)
        # extra connections
        self.backend.actions_holder.setViewer(self.actions_view)
        self.traj_view.itemPicked.connect(self.backend.actions_holder.switchModel)
        self.traj_view.itemPicked.connect(self.setCurrentObject)
        #
        self.actions_view.execute_action.connect(self.runAction)
        self.actions_view.setModel(self.backend.actions_holder.current_model)

    def attachActions(self):
        self.file_name_for_loading.connect(self.backend.loadFile)
        self.backend.selected_converter.connect(self.convertTrajectory)

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
        loader = LoaderButton(backend=self)
        loader.setIcon(self.resources._icons["plus"])
        loader.load_hdf.connect(self.loadTrajectory)
        self.loader_button = loader
        self._toolBar.addWidget(loader)
        self._toolbar_buttons.append((loader, "plus"))
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

    @Slot(DataTreeItem)
    def setCurrentObject(self, data_object: DataTreeItem):
        self.current_object = data_object
        try:
            filename = os.path.join(
                data_object.file_info.absolute_path, data_object.file_info.filename
            )
        except AttributeError:
            filename = data_object.file.text()
        self._visualiser._new_trajectory(filename)

    @Slot(bool)
    def invertToolbar(self, dark=False):
        if dark:
            for obj, key in self._toolbar_buttons:
                obj.setIcon(self.resources._inverted_icons[key])
        else:
            for obj, key in self._toolbar_buttons:
                obj.setIcon(self.resources._icons[key])

    def createTrajectoryViewer(self):
        base, temp = self.wid_gen.wrapWidget(
            cls=TrajectoryViewer, parent=self, dockable=True, name="Trajectories"
        )
        self.traj_view = temp
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, base)
        self._views["trajectory"].append(temp)

    def createMolecularViewer(self):
        base, temp = self.wid_gen.wrapWidget(
            cls=ViewerControls, parent=self, dockable=True, name="3D View"
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, base)
        viewer = MolecularViewer(temp)
        temp.setViewer(viewer)
        self._visualiser = viewer

    def createJobsViewer(self):
        base, temp = self.wid_gen.wrapWidget(
            cls=QTreeView, parent=self, dockable=True, name="Jobs"
        )
        self.job_view = temp
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, base)
        self._views["jobs"].append(temp)

    def createActionsViewer(self):
        base, temp = self.wid_gen.wrapWidget(
            cls=ActionsTree, parent=self, dockable=True, name="Actions"
        )
        self.actions_view = temp
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, base)
        self._views["actions"].append(temp)

    @Slot()
    def saveSettings(self):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("state", self.saveState())
        self.settings.endGroup()

    def reportError(self, text: str):
        print(text)
