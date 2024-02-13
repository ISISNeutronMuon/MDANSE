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
from qtpy.QtCore import Slot, QObject, QMutex, Signal

from MDANSE.__pkginfo__ import __author__, __commit__, __version__, __beta__
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


from MDANSE_GUI.DataViewModel.TrajectoryHolder import DataTreeModel
from MDANSE_GUI.DataViewModel.JobHolder import JobHolder
from MDANSE_GUI.DataViewModel.ActionsHolder import ActionsSuperModel


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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lock = QMutex()
        self.data_holders = {}
        self.createTrajectoryHolder()
        self.createJobHolder()
        self.createActionsHolder()

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
            ]
        )

    def createJobHolder(self):
        self.job_holder = JobHolder(parent=self)
        self.data_holders["jobs"] = self.job_holder

    @Slot(str)
    def loadFile(self, fname: str):
        ic(f"LoadFile triggered in BackEnd. File name is {fname}.")
        if len(fname) < 2:
            ic(f"Strangely short file name - not proceeding.")
            return None
        self.new_trajectory.emit(fname)

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
