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
import logging
from logging import Handler
from logging.handlers import QueueListener
from multiprocessing import Pipe, Queue, Event

from icecream import ic

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QTimer, QThread, QMutex, Qt

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE_GUI.Subprocess.Subprocess import Subprocess, Connection
from MDANSE_GUI.Subprocess.JobState import (
    Starting,
    Finished,
    Running,
    Failed,
    Paused,
    Aborted,
)
from MDANSE_GUI.Subprocess.JobStatusProcess import JobStatusProcess, JobCommunicator
from MDANSE.MLogging import FMT


LOG = logging.getLogger("MDANSE")


class JobThread(QThread):

    def __init__(
        self,
        job_comm: "JobCommunicator",
        receiving_end: "Connection",
        subprocess_reference: "Subprocess",
    ):
        super().__init__()
        self._job_comm = job_comm
        self._pipe_end = receiving_end
        self._subprocess = subprocess_reference
        self._keep_running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self.check_if_alive)
        self._timer.setInterval(2000)

    def start(self, *args, **kwargs) -> None:
        retval = super().start(*args, **kwargs)
        self._timer.start()
        return retval

    def fail(self):
        self._job_comm.status_update(("COMMUNICATION", False))
        self._keep_running = False
        self._timer.stop()
        self.terminate()

    @Slot()
    def check_if_alive(self):
        if not self._subprocess.is_alive():
            self.fail()

    def run(self):
        while self._keep_running:
            try:
                status_update = self._pipe_end.recv()
            except:
                self.fail()
            else:
                self._job_comm.status_update(status_update)


class JobEntry(Handler, QObject):
    """This coordinates all the objects that make up one line on the list
    of current jobs. It is used for reporting the task progress to the GUI."""

    def __init__(self, command=None, entry_number=0, pause_event=None):
        super().__init__()
        QObject.__init__(self)
        self._command = command
        self._parameters = {}
        self._pause_event = pause_event
        # state pattern
        self._current_state = Starting(self)
        self._Starting = Starting(self)
        self._Finished = Finished(self)
        self._Aborted = Aborted(self)
        self._Running = Running(self)
        self._Failed = Failed(self)
        self._Paused = Paused(self)
        # other variables
        self.percent_complete = 0
        self._entry_number = entry_number
        self.total_steps = 99
        self._prog_item = QStandardItem()
        self._stat_item = QStandardItem()
        for item in [self._stat_item]:
            item.setData(entry_number)
        self._prog_item.setData(0, role=Qt.ItemDataRole.UserRole)
        self._prog_item.setData("progress", role=Qt.ItemDataRole.DisplayRole)
        self.msgs = ""

    def text_summary(self) -> str:
        result = ""
        result += f"Job type: {self._command}\n"
        result += "Parameters:\n"
        for key, value in self._parameters.items():
            result += f" - {key} = {value}\n"
        result += "Status:\n"
        result += f"Current state: {self._current_state._label}\n"
        result += f"Percent complete: {self.percent_complete}\n"
        return result

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def parameters(self, input: dict):
        self._parameters = input

    def update_fields(self):
        self._prog_item.setText(f"{self.percent_complete} percent complete")
        self._prog_item.setData(self.percent_complete, role=Qt.ItemDataRole.UserRole)
        self._stat_item.setText(self._current_state._label)

    @Slot(bool)
    def on_finished(self, success: bool):
        if success:
            self._current_state.finish()
        else:
            self._current_state.fail()
        self.update_fields()

    @Slot(int)
    def on_started(self, target_steps: int):
        print(f"Item received on_started: {target_steps} total steps")
        self.total_steps = target_steps
        self._current_state.start()
        self.update_fields()

    @Slot(int)
    def on_update(self, completed_steps: int):
        # print(f"completed {completed_steps} out of {self.total_steps} steps")
        if self.total_steps > 0:
            self.percent_complete = round(99 * completed_steps / self.total_steps, 1)
        else:
            self.percent_complete = 0
        self.update_fields()
        self._prog_item.emitDataChanged()

    @Slot()
    def on_oscillate(self):
        """For jobs with unknown duration, the progress bar will bounce."""

    def pause_job(self):
        self._current_state.pause()
        self.update_fields()

    def unpause_job(self):
        self._current_state.unpause()
        self.update_fields()

    def terminate_job(self):
        self._current_state.terminate()
        self.update_fields()

    def kill_job(self):
        self._current_state.kill()
        self.update_fields()

    def emit(self, record):
        msg = self.format(record)
        if self.msgs:
            self.msgs += msg + "\n"
        else:
            self.msgs = msg + "\n"


class JobHolder(QStandardItemModel):
    """All the job INSTANCES that are started by the GUI
    are added to this model."""

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.lock = QMutex()
        self.existing_threads = {}
        self.existing_processes = {}
        self.existing_jobs = {}
        self.existing_listeners = {}
        self._next_number = 0

    @Slot(str)
    def reportError(self, err: str):
        ic(err)

    @property
    def next_number(self):
        retval = int(self._next_number)
        self._next_number += 1
        return retval

    @Slot(list)
    def startProcess(self, job_vars: list):
        log_queue = Queue()

        main_pipe, child_pipe = Pipe()
        main_queue = Queue()
        pause_event = Event()
        entry_number = self.next_number

        item_th = JobEntry(
            command=job_vars[0], entry_number=entry_number, pause_event=pause_event
        )
        item_th.setFormatter(FMT)
        item_th.setLevel("INFO")

        try:
            subprocess_ref = Subprocess(
                job_name=job_vars[0],
                job_parameters=job_vars[1],
                pipe=child_pipe,
                queue=main_queue,
                pause_event=pause_event,
                log_queue=log_queue
            )
        except:
            ic(f"Failed to create Subprocess using {job_vars}")
            return

        listener = QueueListener(log_queue, item_th, respect_handler_level=True)
        listener.start()

        communicator = JobCommunicator()
        watcher_thread = JobThread(communicator, main_pipe, subprocess_ref)
        communicator.moveToThread(watcher_thread)

        item_th.parameters = job_vars[1]
        communicator.target.connect(item_th.on_started)  # int
        communicator.progress.connect(item_th.on_update)  # int
        communicator.finished.connect(item_th.on_finished)  # bool
        communicator.oscillate.connect(item_th.on_oscillate)  # nothing
        LOG.info("Watcher thread ready to start!")
        watcher_thread.start()
        try:
            task_name = str(job_vars[0])
        except:
            task_name = str("This should have been a job name")
        name_item = QStandardItem(task_name)
        name_item.setData(entry_number, role=Qt.ItemDataRole.UserRole)
        self.appendRow(
            [
                name_item,
                item_th._prog_item,
                item_th._stat_item,
            ]
        )
        # nrows = self.rowCount()
        # index = self.indexFromItem(item_th._item)
        # print(f"Index: {index}")
        self.existing_processes[entry_number] = subprocess_ref
        self.existing_threads[entry_number] = watcher_thread
        self.existing_jobs[entry_number] = item_th
        self.existing_listeners[entry_number] = listener
        LOG.info("Subprocess ready to start!")
        subprocess_ref.start()
