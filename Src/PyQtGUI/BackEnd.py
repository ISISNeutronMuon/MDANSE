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

from PyQt6.QtCore import pyqtSlot, QObject, QThread, QMutex, pyqtSignal, QProcess

from MDANSE.PyQtGUI.DataViewModel.TrajectoryHolder import TrajectoryHolder
from MDANSE.PyQtGUI.DataViewModel.JobHolder import JobHolder

class BackEnd(QObject):
    """The main window of the MDANSE GUI,
    inherits QMainWindow.

    Args:
        QMainWindow - the base class.
    """
    
    def __init__(self, parent = None, python = ""):
        super().__init__(parent)

        self.data_holders = {}
        self.python_interpreter = python  # we need it to call scripts
        # ^^^^^^^^^^^^^^^
        # This dictionary will hold all the objects derived from
        # the QStandardDataModel, which can be connected to GUI components.
        # The keys of the dictionary should match the keys of the 
        # FrontEnd's self.views dictionary.
        self.createTrajectoryHolder()
        self.createJobHolder()

    def createTrajectoryHolder(self):
        self.trajectory_holder = TrajectoryHolder(parent=self)
        self.data_holders['trajectory'] = self.trajectory_holder

    def createJobHolder(self):
        self.job_holder = JobHolder(parent=self, python = self.python_interpreter)
        self.data_holders['jobs'] = self.job_holder

    def getActions(self):
        callable_slots =[
            [self.loadFile, 'Load File'],
            [self.startJob, 'Start a Job'],
        ]
        return callable_slots

    @pyqtSlot()
    def loadFile(self):
        print("LoadFile triggered in BackEnd.")

    @pyqtSlot()
    def startJob(self):
        print("startJob triggered in BackEnd.")
        pass  # whatever happens here, a QProcess will be involved at some point


        