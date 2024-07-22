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

import collections
import pickle
import os
import threading
import time

from MDANSE import PLATFORM
from MDANSE.Framework.Status import Status


class JobState(collections.OrderedDict):
    pass


class JobStatus(Status):
    def __init__(self, job):
        Status.__init__(self)

        self._state = JobState()
        self._state["pid"] = PLATFORM.pid()
        self._state["type"] = job.__class__.__name__
        self._state["start"] = str(time.time())
        self._state["elapsed"] = "N/A"
        self._state["current_step"] = 0
        self._state["n_steps"] = 0
        self._state["progress"] = 0
        self._state["state"] = "running"
        self._state["name"] = job.name
        self._state["traceback"] = ""
        self._state["temporary_file"] = None
        self._state["info"] = ""

        self.save_status()

    def finish_status(self):
        pass

    @property
    def state(self):
        return self._state

    def cleanup(self):
        pass

    def start_status(self):
        self._state["n_steps"] = self.nSteps

        self.save_status()

    def save_status(self):
        pass

    def stop_status(self):
        pass

    def update_status(self):
        self._state["elapsed"] = self.elapsedTime
        self._state["current_step"] = self.currentStep
        if self._nSteps is not None:
            self._state["progress"] = 100 * self.currentStep / self.nSteps
        else:
            self._state["progress"] = 0

        self.save_status()

    def fixed_status(self, current_progress: int):
        pass
