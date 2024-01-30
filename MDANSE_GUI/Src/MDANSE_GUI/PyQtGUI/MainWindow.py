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
    QSize,
    QMetaObject,
    QLocale,
    QObject,
    QThread,
    QMutex,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    QPoint,
    Signal,
)
from qtpy.QtGui import QFont, QAction, QEnterEvent
from qtpy.QtWidgets import (
    QFrame,
    QTabWidget,
    QSizePolicy,
    QApplication,
    QMainWindow,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QHBoxLayout,
    QAbstractItemView,
    QFileDialog,
    QLabel,
    QToolBar,
    QMenu,
    QWidgetAction,
    QTreeView,
)

from MDANSE_GUI.PyQtGUI.BackEnd import BackEnd
from MDANSE_GUI.PyQtGUI.DataViewModel.TrajectoryHolder import DataTreeItem
from MDANSE_GUI.PyQtGUI.Widgets.Generator import WidgetGenerator
from MDANSE_GUI.PyQtGUI.Widgets.ConvertDialog import ConverterDialog
from MDANSE_GUI.PyQtGUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.PyQtGUI.Widgets.ActionsTree import ActionsTree
from MDANSE_GUI.PyQtGUI.Resources import Resources
from MDANSE_GUI.PyQtGUI.UnitsEditor import UnitsEditor
from MDANSE_GUI.PyQtGUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE_GUI.PyQtGUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE_GUI.PyQtGUI.Widgets.TrajectoryViewer import TrajectoryViewer
from MDANSE_GUI.PyQtGUI.MolecularViewer.MolecularViewer import MolecularViewer
from MDANSE_GUI.PyQtGUI.MolecularViewer.Controls import ViewerControls
from MDANSE_GUI.PyQtGUI.Widgets.StyleDialog import StyleDialog, StyleDatabase
from MDANSE_GUI.PyQtGUI.pygenplot.widgets.main_window import MainWindow


class LoaderButton(QToolButton):
    """Subclassed from QToolButton, this object shows the name of a
    chemical element, and creates a pop-up menu giving access to information
    about isotopes when clicked.
    """

    load_hdf = Signal()
    start_converter = Signal(str)

    def __init__(self, *args, caption="Load", backend=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setText(caption)
        # self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.converter_source = backend

        self.clicked.connect(self.altContextMenu)

    # def enterEvent(self, a0: QEnterEvent) -> None:
    #     self.atom_info.emit(self.info)
    #     return super().enterEvent(a0)

    def populateMenu(self, menu: QMenu):
        hdf_action = menu.addAction("Load Trajectory File")
        hdf_action.triggered.connect(self.load_hdf)
        menu.addSeparator()
        for cjob in self.converter_source.backend.getConverters():
            menu.addAction("Convert using " + str(cjob))

    def altContextMenu(self):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(self.mapToGlobal(QPoint(10, 10)))
        if res is not None and "Load Trajectory File" != res.text():
            self.start_converter.emit(res.text())

    def contextMenuEvent(self, event):
        menu = QMenu()
        self.populateMenu(menu)
        res = menu.exec_(event.globalPos())
        if res is not None and "Load Trajectory File" != res.text():
            self.start_converter.emit(res.text())


class Main(QMainWindow):
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
        self.makeBasicLayout()
        self.workdir = os.path.expanduser("~")
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
        # self.traj_view.itemPicked.connect(self.actions_view.showValidActions)

    def attachActions(self):
        self.file_name_for_loading.connect(self.backend.loadFile)
        self.converter_name_for_dialog.connect(self.backend.returnConverter)
        self.loader_button.start_converter.connect(self.backend.returnConverter)
        self.backend.selected_converter.connect(self.convertTrajectory)

    def makeBasicLayout(self):
        self.createTrajectoryViewer()
        self.createJobsViewer()
        self.createActionsViewer()
        self.setupMenubar()
        self.setupToolbar()
        self.createMolecularViewer()

    def setupMenubar(self):
        self._menuBar = self.menuBar()
        self._menuBar.setObjectName("main menubar")
        self._menuBar.setVisible(True)
        self.exitAct = QAction("Exit", parent=self._menuBar)
        self.exitAct.triggered.connect(self.destroy)
        self._menuBar.addAction(self.exitAct)

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
            print(f"fname[0]:{fname[0]}")
            print(f"fname[1]:{fname[1]}")
            self.file_name_for_loading.emit(fname[0])

    @Slot(object)
    def convertTrajectory(self, converter=None):
        ic(f"Received converter: {converter}")
        dialog = ConverterDialog
        dialog_instance = dialog(self, converter=converter)
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        result = dialog_instance.exec()

    @Slot(object)
    def runAction(self, converter=None):
        ic(f"Received action: {converter}")
        dialog = ActionDialog
        dialog_instance = dialog(
            self, converter=converter, source_object=self.current_object
        )
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        result = dialog_instance.exec()

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

    def onMyToolBarButtonClick(self, s):
        print("click", s)
