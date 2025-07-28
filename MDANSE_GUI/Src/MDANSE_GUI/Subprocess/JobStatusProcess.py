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
from __future__ import annotations

import os
import time
from contextlib import suppress
from multiprocessing import Queue
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Event

from qtpy.QtCore import QObject, Signal, Slot

from MDANSE.Framework.Jobs.JobStatus import JobInfo, JobStates
from MDANSE.Framework.Status import Status
from MDANSE.MLogging import LOG


class JobCommunicator(QObject):
    target = Signal(int)
    progress = Signal(int)
    finished = Signal(bool)
    oscillate = Signal()

    def status_update(self, state: JobInfo):
        """Update relevant status windows.

        Parameters
        ----------
        state : JobInfo
            Current state of job.

        Raises
        ------
        NotImplementedError
            Paused is not currently supported in this interface.
        """
        if state.state is JobStates.STARTING:
            if state.n_steps is not None:
                self.target.emit(state.n_steps)
            else:
                self.oscillate.emit()

        elif state.state is JobStates.RUNNING:
            self.progress.emit(state.progress)

        elif state.state is JobStates.ABORTED:
            self.finished.emit(False)
            self.terminate_the_process()

        elif state.state is JobStates.FAILED:
            LOG.info(f"Communication with the subprocess is now {False}")
            self.finished.emit(False)
            self.terminate_the_process()

        elif state.state is JobStates.PAUSED:
            raise NotImplementedError()

        elif state.state is JobStates.FINISHED:
            self.finished.emit(True)
            self.terminate_the_process()

    @Slot()
    def terminate_the_process(self):
        """Kill a running job."""
        LOG.info(f"JobCommunicator PID: {os.getpid()} started 'terminate_the_process'")
        try:
            self._process.terminate()
        except Exception:
            return
        else:
            try:
                self._process.close()
            except Exception:
                return


class JobStatusProcess(Status):
    def __init__(
        self,
        job_name: str,
        pipe: Connection,
        queue_0: Queue,
        queue_1: Queue,
        pause_event: Event,
        **kwargs,
    ):
        super().__init__()
        self._pipe = pipe
        self._queue_0 = queue_0
        self._queue_1 = queue_1

        self._state = JobInfo(
            name=job_name,
            type=None,
            start=time.time(),
            elapsed="N/A",
            n_steps=self._nSteps,
        )

        self._pause_event = pause_event
        self._pause_event.set()

    @property
    def state(self):
        return self._state

    @property
    def job_state(self) -> JobStates:
        """Alias for current job state."""
        return self.state.state

    @job_state.setter
    def job_state(self, value: JobStates):
        self.state.state = value

    def finish_status(self):
        """Assert finished state."""
        self.job_state = JobStates.FINISHED
        self.state.end = time.time()
        self._pipe.send(self.state)

    def start_status(self):
        """Assert started state."""
        LOG.info(f"JobStatusProcess PID: {self.state.pid} started 'start_status'")

        with suppress(ValueError):
            self.state.n_steps = int(self._nSteps)

        self.job_state = JobStates.STARTING
        self._pipe.send(self.state)
        # self._updateStep = 1

    def stop_status(self):
        """Assert aborted state."""
        self.job_state = JobStates.ABORTED
        self._pipe.send(self.state)

    def update_status(self):
        """Assert one step is done."""
        self.job_state = JobStates.RUNNING
        self.state.current_step += 1
        self.state.progress = int(self.state.current_step) * self._updateStep
        self._pipe.send(self.state)

    def fixed_status(self, current_progress: int):
        """Assert current step is X and done."""
        self.job_state = JobStates.RUNNING
        self.state.current_step = current_progress
        self.state.progress = int(self.state.current_step) * self._updateStep
        self._pipe.send(self.state)
