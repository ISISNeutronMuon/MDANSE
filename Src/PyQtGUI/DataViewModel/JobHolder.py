# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/DataViewModel/JobHolder.py
# @brief     Subclass of QStandardItemModel for MDANSE jobs
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, QProcess


class JobItem(QStandardItem):

    def __init__(self, *args, command = None):
        super().__init__(*args)
        self._command = command


class JobHolder(QStandardItemModel):

    def __init__(self, parent: QObject = None, python: str = ""):
        super().__init__(parent=parent)
        self.python_interpreter = python

    @Slot(object)
    def addItem(self, new_entry: QProcess):
        traj = JobItem(new_entry.basename, trajectory = new_entry)
        self.appendRow([traj])
    
    @Slot(int)
    def startJob(self, job_id: int = -1):
        handle = QProcess(parent=self)

