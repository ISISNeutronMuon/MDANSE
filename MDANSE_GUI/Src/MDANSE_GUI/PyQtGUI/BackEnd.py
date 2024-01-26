# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/BackEnd.py
# @brief     Everything that is not GUI is accessed through the BackEnd
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

import copy
from icecream import ic
from qtpy.QtCore import Slot, QObject, QThread, QMutex, Signal, QProcess

from MDANSE.__pkginfo__ import __author__, __commit__, __version__, __beta__
from MDANSE.Core.Platform import PLATFORM
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.Framework.Handlers.IHandler import IHandler
from MDANSE.Framework.InputData.IInputData import IInputData
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable
from MDANSE.Framework.Projectors.IProjector import IProjector
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.Selectors.ISelector import ISelector


from MDANSE_GUI.PyQtGUI.DataViewModel.TrajectoryHolder import DataTreeModel
from MDANSE_GUI.PyQtGUI.DataViewModel.JobHolder import JobHolder
from MDANSE_GUI.PyQtGUI.DataViewModel.ActionsHolder import ActionsSuperModel


class BackEnd(QObject):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    new_trajectory = Signal(str)
    all_converters = Signal(object)
    selected_converter = Signal(object)
    selected_action = Signal(object)

    def __init__(self, parent=None, python=""):
        super().__init__(parent)

        self.lock = QMutex()
        self.data_holders = {}
        self.python_interpreter = python  # we need it to call scripts
        # ^^^^^^^^^^^^^^^
        # This dictionary will hold all the objects derived from
        # the QStandardDataModel, which can be connected to GUI components.
        # The keys of the dictionary should match the keys of the
        # FrontEnd's self.views dictionary.
        self.createTrajectoryHolder()
        self.createJobHolder()
        self.createActionsHolder()
        self._converters = []
        self._reverse_converters = {}  # internal dictionary for finding converters
        self.checkConverters()
        self._actions = []
        self._reverse_actions = {}  # internal dictionary for finding converters
        self.checkActions()

    def createTrajectoryHolder(self):
        self.trajectory_holder = DataTreeModel(parent=self)
        self.data_holders["trajectory"] = self.trajectory_holder
        self.new_trajectory.connect(self.trajectory_holder.acceptNewTrajectory)

    def createActionsHolder(self):
        self.actions_holder = ActionsSuperModel(parent=self)
        self.actions_holder.buildModels(
            [
                IJob,
                Converter,
                IInstrumentResolution,
                IConfigurator,
                IFormat,
                IHandler,
                IInputData,
                IOutputVariable,
                IProjector,
                IQVectors,
                ISelector,
            ]
        )
        # self.data_holders['actions'] = self.trajectory_holder

    def createJobHolder(self):
        self.job_holder = JobHolder(parent=self, python=self.python_interpreter)
        self.data_holders["jobs"] = self.job_holder

    def getActions(self):
        callable_slots = [
            [self.loadFile, "Load File"],
            [self.startJob, "Start a Job"],
        ]
        return callable_slots

    @Slot(str)
    def loadFile(self, fname: str):
        ic(f"LoadFile triggered in BackEnd. File name is {fname}.")
        if len(fname) < 2:
            ic(f"Strangely short file name - not proceeding.")
            return None
        self.new_trajectory.emit(fname)

    @Slot()
    def startJob(self):
        ic("startJob triggered in BackEnd.")
        pass  # whatever happens here, a QProcess will be involved at some point

    def checkConverters(self):
        ic("checkConverters triggered in BackEnd.")
        self.lock.lock()
        self._converters = []
        self._reverse_converters = {}
        for key, conv in Converter.indirect_subclass_dictionary().items():
            ic(f"key:{key}, val:{conv}")
            self._converters.append(key)
            self._reverse_converters[str(key)] = Converter.create(str(key))
        self.lock.unlock()

    def getConverters(self):
        ic("getConverters triggered in BackEnd.")
        temp = None
        self.lock.lock()
        temp = copy.deepcopy(self._converters)
        self.lock.unlock()
        return temp

    @Slot(str)
    def returnConverter(self, key: str):
        """This slot will make Backend emit a signal that will
        create a Dialog for a specific trajectory converter.
        The type of the converter is chosen by the 'key' input
        parameter.

        Arguments:
            key -- a string specifying which converter is needed.
        """
        # ic("returnConverter has been triggered in BackEnd - but what for?")
        thing = self._reverse_converters[str(key).split()[-1]]
        self.selected_converter.emit(thing)

    def checkActions(self):
        ic("checkActions triggered in BackEnd.")
        self.lock.lock()
        self._actions = []
        self._reverse_actions = {}
        for key, act in IJob.indirect_subclass_dictionary().items():
            ic(f"key:{key}, val:{act}")
            self._actions.append(act)
            self._reverse_actions[str(act)] = IJob.create(str(key))
        self.lock.unlock()

    def getActions(self):
        ic("getActions triggered in BackEnd.")
        temp = None
        self.lock.lock()
        temp = copy.deepcopy(self._actions)
        self.lock.unlock()
        return temp

    @Slot(str)
    def returnActions(self, key: str):
        """This slot will make Backend emit a signal that will
        create a Dialog for a specific trajectory converter.
        The type of the converter is chosen by the 'key' input
        parameter.

        Arguments:
            key -- a string specifying which converter is needed.
        """
        ic("returnActions has been triggered in BackEnd")
        thing = self._reverse_actions[str(key).split()[-1]]
        self.selected_action.emit(thing)
