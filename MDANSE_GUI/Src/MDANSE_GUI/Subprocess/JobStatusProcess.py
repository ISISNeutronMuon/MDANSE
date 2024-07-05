#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os
from typing import Tuple
from multiprocessing import Queue
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event

from qtpy.QtCore import QObject, Slot, Signal

from MDANSE.MLogging import LOG
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
            self.terminate_the_process()
        elif key == "STEP":
            self.progress.emit(value)
        elif key == "STARTED":
            if value is not None:
                self.target.emit(value)
            else:
                self.oscillate.emit()
        elif key == "COMMUNICATION":
            LOG.info(f"Communication with the subprocess is now {value}")
            self.finished.emit(value)
            self.terminate_the_process()

    @Slot()
    def terminate_the_process(self):
        LOG.info(f"JobCommunicator PID: {os.getpid()} started 'terminate_the_process")
        try:
            self._process.terminate()
        except:
            return
        else:
            try:
                self._process.close()
            except:
                return


class JobStatusProcess(Status):
    def __init__(
        self,
        pipe: "Connection",
        queue: Queue,
        pause_event: "Event",
        **kwargs,
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
        self._pipe.send(("FINISHED", True))

    def start_status(self):
        LOG.info(f"JobStatusProcess PID: {os.getpid()} started 'start_status")
        try:
            temp = int(self._nSteps)
        except:
            self._pipe.send(("STARTED", None))
        else:
            self._pipe.send(("STARTED", temp))
        # self._updateStep = 1

    def stop_status(self):
        self._pipe.send(("FINISHED", False))

    def update_status(self):
        self._progress_meter += 1
        temp = int(self._progress_meter) * self._updateStep
        self._pipe.send(("STEP", temp))

    def fixed_status(self, current_progress: int):
        temp = int(current_progress) * self._updateStep
        self._pipe.send(("STEP", temp))
