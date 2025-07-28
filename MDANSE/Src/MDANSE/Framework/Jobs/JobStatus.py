#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Literal, TypedDict

from MDANSE import PLATFORM
from MDANSE.Framework.Status import Status


class JobStates(Enum):
    """Possible states of jobs."""

    STARTING = auto()
    RUNNING = auto()
    ABORTED = auto()
    FAILED = auto()
    PAUSED = auto()
    FINISHED = auto()


ALLOWED_ACTIONS = {
    JobStates.RUNNING: {"Pause", "Terminate", "Kill"},
    JobStates.ABORTED: {"Delete"},
    JobStates.FAILED: {"Delete"},
    JobStates.FINISHED: {"Delete"},
    JobStates.STARTING: {"Pause", "Terminate", "Kill"},
    JobStates.PAUSED: {"Resume", "Terminate", "Kill"},
}


@dataclass(eq=False)  # With 3.10 add: slots=True, kw_only=True
class JobInfo:
    """Current state of job."""

    name: str | None = None
    pid: int = PLATFORM.pid()
    type: str | None = None
    start: float | None = None
    end: float | None = None
    elapsed: float | Literal["N/A"] = "N/A"
    rate: float | Literal["N/A"] = "N/A"
    pct_rate: float | Literal["N/A"] = "N/A"
    current_step: int = 0
    n_steps: int = 0
    progress: float = 0
    state: JobStates | str | None = None
    traceback: str = ""
    temporary_file: str | None = None
    info: str = ""


class JobStatus(Status):
    def __init__(self, job):
        Status.__init__(self)

        self._state = JobInfo(
            name=job.name,
            type=type(job).__name__,
            start=time.time(),
            state=JobStates.RUNNING,
        )

        self.save_status()

    def finish_status(self):
        self.state.end = time.time()

    @property
    def state(self):
        return self._state

    def cleanup(self):
        pass

    def start_status(self):
        self._state.n_steps = self.nSteps

        self.save_status()

    def save_status(self):
        pass

    def stop_status(self):
        pass

    def update_status(self):
        self._state.elapsed = self.elapsedTime
        self._state.current_step = self.currentStep
        if self._nSteps is not None:
            self._state.progress = 100 * self.currentStep / self.nSteps
        else:
            self._state.progress = 0
        try:
            self._state.rate = self._state.current_step / self._state.elapsed
            self._state.pct_rate = self._state.progress / self._state.elapsed
        except TypeError:
            self._state.rate = self._state.pct_rate = "N/A"
        self.save_status()

    def fixed_status(self, current_progress: int):
        pass
