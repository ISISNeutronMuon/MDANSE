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

from typing import Tuple
from multiprocessing import Pipe, Queue, Process, Event
from multiprocessing.connection import Connection

from icecream import ic
from qtpy.QtCore import QObject, Slot, Signal, QProcess, QThread, QMutex

from MDANSE.Framework.Status import Status


class JobCommunicator(QObject):
    target = Signal(int)
    progress = Signal(int)
    finished = Signal(bool)
    oscillate = Signal()

    def status_update(self, input: Tuple):
        key, value = input
        if key == "FINISHED":
            self.finished.emit(value)
        elif key == "STEP":
            self.progress.emit(value)
        elif key == "STARTED":
            if value is not None:
                self.target.emit(value)
            else:
                self.oscillate.emit()
        elif key == "COMMUNICATION":
            print(f"Communication with the subprocess is now {value}")
            self.finished.emit(value)


class JobStatusProcess(Status):
    def __init__(
        self, pipe: "Connection", queue: Queue, pause_event: "Event", **kwargs
    ):
        super().__init__()
        self._pipe = pipe
        self._queue = queue
        self._state = {}  # for compatibility with JobStatus
        self._progress_meter = 0
        self._pause_event = pause_event
        self._pause_event.set()

    @property
    def state(self):
        return self._state

    def finish_status(self):
        ic()
        self._pipe.send(("FINISHED", True))

    def start_status(self):
        ic()
        try:
            temp = int(self._nSteps)
        except:
            self._pipe.send(("STARTED", None))
        else:
            self._pipe.send(("STARTED", temp))
        # self._updateStep = 1

    def stop_status(self):
        ic()
        self._pipe.send(("FINISHED", False))

    def update_status(self):
        self._progress_meter += 1
        temp = int(self._progress_meter) * self._updateStep
        self._pipe.send(("STEP", temp))
