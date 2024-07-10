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
from qtpy.QtCore import QObject, Signal, QMutex

from MDANSE.Framework.Status import Status


class JobCommunicator(QObject):
    target = Signal(int)
    progress = Signal(int)
    finished = Signal(bool)
    oscillate = Signal()


class JobStatusQt(Status):
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
        self._communicator.finished.emit(True)

    def start_status(self):
        try:
            temp = int(self._nSteps)
        except:
            self._communicator.oscillate.emit()
        else:
            self._communicator.target.emit(temp)

    def stop_status(self):
        self._communicator.finished.emit(False)

    def update_status(self):
        self._mutex.lock()
        self._progress_meter += 1
        temp = int(self._progress_meter)
        self._mutex.unlock()
        self._communicator.progress.emit(temp)
