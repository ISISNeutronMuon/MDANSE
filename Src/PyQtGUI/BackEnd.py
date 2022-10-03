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
    
    def __init__(self, parent = None):
        super().__init__(parent)

        self.data_holders = {}
        # ^^^^^^^^^^^^^^^
        # This dictionary will hold all the objects derived from
        # the QStandardDataModel, which can be connected to GUI components.
        # The keys of the dictionary should match the keys of the 
        # FrontEnd's self.views dictionary.
        self.createTrajectoryHolder()

    def createTrajectoryHolder(self):
        self.trajectory_holder = TrajectoryHolder(parent=self)
        self.data_holders['trajectory'] = self.trajectory_holder

    def createJobHolder(self):
        self.job_holder = JobHolder(parent=self)
        self.data_holders['jobs'] = self.job_holder

    def startJob(self):
        pass  # whatever happens here, a QProcess will be involved at some point


        