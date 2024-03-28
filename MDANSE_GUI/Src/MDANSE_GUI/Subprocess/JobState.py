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
from abc import ABC, abstractmethod


class JobState(ABC):

    _label = "JobState"
    _allowed_actions = []

    def __init__(self, parent):
        self._parent = parent

    @abstractmethod
    def pause(self):
        """Pauses the process"""

    @abstractmethod
    def unpause(self):
        """Resumes the process execution"""

    @abstractmethod
    def start(self):
        """Starts the process"""

    @abstractmethod
    def terminate(self):
        """Instructs the process to stop"""

    @abstractmethod
    def kill(self):
        """Stops the process the hard way"""

    @abstractmethod
    def finish(self):
        """Reach the end of the run successfully"""

    @abstractmethod
    def fail(self):
        """Break down on before finishing"""


class Running(JobState):

    _label = "Running"
    _allowed_actions = [
        "Pause",
        "Terminate",
        "Kill",
    ]

    def pause(self):
        """Pauses the process"""
        self._parent._pause_event.clear()
        self._parent._current_state = self._parent._Paused

    def unpause(self):
        """Resumes the process execution"""

    def start(self):
        """Starts the process"""

    def terminate(self):
        """Instructs the process to stop"""
        self._parent._current_state = self._parent._Aborted

    def kill(self):
        """Stops the process the hard way"""
        self._parent._current_state = self._parent._Aborted

    def finish(self):
        """Reach the end of the run successfully"""
        self._parent.percent_complete = 100
        self._parent._current_state = self._parent._Finished

    def fail(self):
        """Break down on before finishing"""
        self._parent._current_state = self._parent._Failed


class Aborted(JobState):

    _label = "Aborted"
    _allowed_actions = ["Delete"]

    def pause(self):
        """Pauses the process"""

    def unpause(self):
        """Resumes the process execution"""

    def start(self):
        """Starts the process"""

    def terminate(self):
        """Instructs the process to stop"""

    def kill(self):
        """Stops the process the hard way"""

    def finish(self):
        """Reach the end of the run successfully"""

    def fail(self):
        """Break down on before finishing"""


class Failed(JobState):

    _label = "Failed"
    _allowed_actions = ["Delete"]

    def pause(self):
        """Pauses the process"""

    def unpause(self):
        """Resumes the process execution"""

    def start(self):
        """Starts the process"""

    def terminate(self):
        """Instructs the process to stop"""

    def kill(self):
        """Stops the process the hard way"""

    def finish(self):
        """Reach the end of the run successfully"""

    def fail(self):
        """Break down on before finishing"""


class Finished(JobState):

    _label = "Finished"
    _allowed_actions = ["Delete"]

    def pause(self):
        """Pauses the process"""

    def unpause(self):
        """Resumes the process execution"""

    def start(self):
        """Starts the process"""

    def terminate(self):
        """Instructs the process to stop"""

    def kill(self):
        """Stops the process the hard way"""

    def finish(self):
        """Reach the end of the run successfully"""

    def fail(self):
        """Break down on before finishing"""


class Starting(JobState):

    _label = "Starting"
    _allowed_actions = [
        "Pause",
        "Terminate",
        "Kill",
    ]

    def pause(self):
        """Pauses the process"""

    def unpause(self):
        """Resumes the process execution"""

    def start(self):
        """Starts the process"""
        self._parent._current_state = self._parent._Running

    def terminate(self):
        """Instructs the process to stop"""

    def kill(self):
        """Stops the process the hard way"""

    def finish(self):
        """Reach the end of the run successfully"""

    def fail(self):
        """Break down on before finishing"""
        self._parent._current_state = self._parent._Failed


class Paused(JobState):

    _label = "Paused"
    _allowed_actions = [
        "Resume",
        "Terminate",
        "Kill",
    ]

    def pause(self):
        """Pauses the process"""

    def unpause(self):
        """Resumes the process execution"""
        self._parent._pause_event.set()
        self._parent._current_state = self._parent._Running

    def start(self):
        """Starts the process"""

    def terminate(self):
        """Instructs the process to stop"""
        self._parent._current_state = self._parent._Aborted

    def kill(self):
        """Stops the process the hard way"""
        self._parent._current_state = self._parent._Aborted

    def finish(self):
        """Reach the end of the run successfully"""
        self._parent.percent_complete = 100
        self._parent._current_state = self._parent._Finished

    def fail(self):
        """Break down on before finishing"""
