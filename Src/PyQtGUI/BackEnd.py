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
 
from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE.__pkginfo__ import __author__, __commit__, __version__, __beta__
from MDANSE.Core.Platform import PLATFORM
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.PyQtGUI.DataViewModel.TrajectoryHolder import DataTreeModel
from MDANSE.PyQtGUI.DataViewModel.JobHolder import JobHolder
from MDANSE.PyQtGUI.RegistryViewer import RegistryTree


class BackEnd(QObject):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """

    new_trajectory = Signal(str)
    all_converters = Signal(object)
    selected_converter = Signal(object)
    
    def __init__(self, parent = None, python = ""):
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
        self.registry = RegistryTree()
        self._converters = []
        self._reverse_converters = {}
        self.checkConverters()

    def createTrajectoryHolder(self):
        self.trajectory_holder = DataTreeModel(parent=self)
        self.data_holders['trajectory'] = self.trajectory_holder
        self.new_trajectory.connect(self.trajectory_holder.acceptNewTrajectory)

    def createJobHolder(self):
        self.job_holder = JobHolder(parent=self, python = self.python_interpreter)
        self.data_holders['jobs'] = self.job_holder

    def getActions(self):
        callable_slots =[
            [self.loadFile, 'Load File'],
            [self.startJob, 'Start a Job'],
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
        for key, conv in self.registry._converters.items():
            ic(f"key:{key}, val:{conv}")
            self._converters.append(conv)
            self._reverse_converters[str(conv)] = REGISTRY['job'][str(key)]
        self.lock.unlock()

    def getConverters(self):
        ic("getConverters triggered in BackEnd.")
        temp = None
        self.lock.lock()
        temp = copy.deepcopy(self._converters)
        self.lock.unlock()
        return temp
    
    @Slot(str)
    def returnConverter(self, key:str):
        ic("returnConverter has been triggered in BackEnd - but what for?")
        # thing = self._reverse_converters[str(key).split()[-1]]
        # self.selected_converter.emit(thing)
