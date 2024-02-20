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

from multiprocessing import Pipe, Queue, Process

from icecream import ic
from qtpy.QtCore import QObject, Slot, Signal, QProcess, QThread, QMutex

from MDANSE.Framework.Status import Status


class JobCommunicator(QObject):
    target = Signal(int)
    progress = Signal(int)
    finished = Signal(bool)
    oscillate = Signal()


class JobStatusProcess(Status):
    def __init__(self, *args, **kwargs):
        qparent = kwargs.pop("parent", None)
        super().__init__()
        self._state = {}  # for compatibility with JobStatus
        self._progress_meter = 0
        self._mutex = QMutex()
        self._communicator = JobCommunicator(parent=qparent)

    @property
    def state(self):
        return self._state

    def finish_status(self):
        ic()
        self._communicator.finished.emit(True)

    def start_status(self):
        ic()
        try:
            temp = int(self._nSteps)
        except:
            self._communicator.oscillate.emit()
        else:
            self._communicator.target.emit(temp)

    def stop_status(self):
        ic()
        self._communicator.finished.emit(False)

    def update_status(self):
        self._mutex.lock()
        self._progress_meter += 1
        temp = int(self._progress_meter)
        self._mutex.unlock()
        self._communicator.progress.emit(temp)
