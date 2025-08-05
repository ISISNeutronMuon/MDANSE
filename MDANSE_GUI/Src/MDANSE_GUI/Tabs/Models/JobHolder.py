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

import time
import traceback
from itertools import count
from logging import Handler
from logging.handlers import QueueListener
from multiprocessing import Event, Pipe, Process, Queue
from typing import Any, NamedTuple

from qtpy.QtCore import QMutex, QObject, Qt, QThread, QTimer, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel

from MDANSE.Framework.Converters import Converter
from MDANSE.Framework.Jobs.JobStatus import JobInfo, JobStates
from MDANSE.MLogging import FMT, LOG
from MDANSE_GUI.Subprocess.JobStatusProcess import JobCommunicator
from MDANSE_GUI.Subprocess.Subprocess import Connection, Subprocess
from MDANSE_GUI.Tabs.Views.Delegates import ProgressDelegate


class JobThread(QThread):
    def __init__(
        self,
        job_comm: JobCommunicator,
        receiving_end: Connection,
        subprocess_reference: Subprocess,
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
        self._job_comm.status_update(JobInfo(state=JobStates.FAILED))
        self._keep_running = False
        self._timer.stop()
        self.terminate()

    @Slot()
    def check_if_alive(self):
        if self._subprocess._closed:
            # The subprocess was closed probably by the user, don't need
            # to keep checking that the subprocess is alive anymore.
            # Also, no need to send out a status update since it should
            # already have been updated already when it got terminated.
            self._keep_running = False
            self._timer.stop()
            self.terminate()
            return
        if not self._subprocess.is_alive():
            self.fail()

    def run(self):
        while self._keep_running:
            try:
                status_update = self._pipe_end.recv()
            except Exception:
                self.fail()
            else:
                self._job_comm.status_update(status_update)


class JobLogHandler(Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def msgs_and_levels(self):
        msgs = []
        levels = []
        for record in self.records:
            msgs.append(self.format(record))
            levels.append(record.levelname)
        return msgs, levels

    def emit(self, record):
        self.records.append(record)


class JobEntry(QObject):
    """This coordinates all the objects that make up one line on the list
    of current jobs. It is used for reporting the task progress to the GUI."""

    for_loading = Signal(str)
    free_filename = Signal(str)

    def __init__(
        self,
        *args,
        command: str | None = None,
        entry_number: int = 0,
        pause_event: Event | None = None,
        load_afterwards: bool = False,
    ):
        super().__init__(*args)

        self._command = command
        self._finished = False
        self.parameters = {}
        self._pause_event = pause_event
        self._load_afterwards = load_afterwards

        self.job = JobInfo(
            name=command,
            start=time.time(),
            state=JobStates.STARTING,
        )

        # Other variables
        self._entry_number = entry_number
        self._prog_item = QStandardItem()
        self._stat_item = QStandardItem()
        self._stat_item.setData(entry_number)

        self._prog_item.setData(0, role=Qt.ItemDataRole.UserRole)
        self._prog_item.setData("progress", role=Qt.ItemDataRole.DisplayRole)
        self._prog_item.setData(0, role=ProgressDelegate.progress_role)
        self._prog_item.setData(100, role=ProgressDelegate.progress_role + 1)
        self.handler = JobLogHandler()

    @staticmethod
    def _sec_fmt(time: float) -> str:
        """Format a time in seconds sensibly."""
        if not isinstance(time, float):
            return "N/A"

        hr, min = divmod(time, 3600)
        min, sec = divmod(min, 60)

        if hr:
            return f"{hr:.0f}hr {min:.0f}m {sec:.0f}s"
        if min:
            return f"{min:.0f}m {sec:.0f}s"

        return f"{sec:.0f}s"

    def text_summary(self) -> str:
        nl = "\n"

        try:
            comp_time = (self.job.n_steps - self.job.current_step) / self.job.rate
        except (TypeError, ZeroDivisionError):
            comp_time = "N/A"

        if self.job.end:
            elapsed_time = self.job.end - self.job.start
        else:
            elapsed_time = time.time() - self.job.start

        return f"""\
Job type: {self._command}
Parameters:
{nl.join(" - {} = {}".format(*kv) for kv in self.parameters.items())}
Status:
  Current state: {self.job.state.name.title()}
  Percent complete: {self.job.progress}
  Percent rate: {self.job.pct_rate} %/s
  Steps: {self.job.current_step}/{self.job.n_steps}
  Step rate: {self.job.rate} steps/s
  Elapsed time: {self._sec_fmt(elapsed_time)}
  Estimated remaining time: {self._sec_fmt(comp_time)}
"""

    def update_fields(self):
        self._prog_item.setText(
            f"{self.job.progress} percent complete ({self.job.pct_rate} %/s)"
        )
        self._prog_item.setData(self.job.progress, role=Qt.ItemDataRole.UserRole)
        self._prog_item.setData(
            int(self.job.current_step),
            role=ProgressDelegate.progress_role,
        )
        self._prog_item.setData(
            self.job.pct_rate,
            role=ProgressDelegate.progress_role + 2,
        )
        self._stat_item.setText(self.job.state.name.title())

    @Slot(bool)
    def on_finished(self, success: bool):
        if self._finished:
            return
        self._finished = True
        file_name = self.expected_output()
        self.job.end = time.time()

        if success:
            if self._load_afterwards:
                self.for_loading.emit(file_name)
            self.finish_job()
        else:
            self.fail_job()

        self.free_filename.emit(file_name)
        self.update_fields()

    def expected_output(self) -> str:
        try:
            len(self.parameters["output_files"][1])
        except TypeError:  # job is a converter
            file_name = self.parameters["output_files"][0]
            if ".mdt" not in file_name[-5:]:
                file_name += ".mdt"
            return file_name
        else:  # job is an analysis
            if "MDAFormat" in self.parameters["output_files"][1]:
                file_name = self.parameters["output_files"][0]
                if ".mda" not in file_name[-5:]:
                    file_name += ".mda"
                return file_name
            else:
                return self.parameters["output_files"][0]

    @Slot(int)
    def on_started(self, target_steps: int):
        LOG.info(f"Item received on_started: {target_steps} total steps")
        self.job.n_steps = target_steps
        self._prog_item.setData(target_steps, role=ProgressDelegate.progress_role + 1)
        self.start_job()

    @Slot(int)
    def on_update(self, completed_steps: int):
        # print(f"completed {completed_steps} out of {self.total_steps} steps")
        self.job.elapsed = time.time() - self.job.start
        if self.job.n_steps > 0:
            self.job.current_step = completed_steps
            self.job.progress = round(99 * self.job.current_step / self.job.n_steps, 1)
            self.job.rate = self.job.current_step / self.job.elapsed
            self.job.pct_rate = self.job.progress / self.job.elapsed

        else:
            self.job.progress = 0

        self.update_fields()
        self._prog_item.emitDataChanged()

    @Slot()
    def on_oscillate(self):
        """For jobs with unknown duration, the progress bar will bounce."""

    def start_job(self):
        self.job.state = JobStates.RUNNING
        self.update_fields()

    def finish_job(self):
        self.job.progress = 100
        self.job.state = JobStates.FINISHED
        self.update_fields()

    def fail_job(self):
        self.job.state = JobStates.FAILED
        self.update_fields()

    def pause_job(self):
        self._pause_event.clear()
        self.job.state = JobStates.PAUSED
        self.update_fields()

    def unpause_job(self):
        self._pause_event.set()
        self.job.state = JobStates.RUNNING
        self.update_fields()

    def terminate_job(self):
        self.job.state = JobStates.ABORTED
        self.update_fields()

    def kill_job(self):
        self.job.state = JobStates.ABORTED
        self.update_fields()


class JobHolder(QStandardItemModel):
    """All the job INSTANCES that are started by the GUI
    are added to this model."""

    trajectory_for_loading = Signal(str)
    results_for_loading = Signal(str)
    protect_filename = Signal(str)
    unprotect_filename = Signal(str)
    new_job_started = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)
        self.lock = QMutex()
        self.jobs: dict[int, Job] = {}
        self.job_number = count()
        self.setHorizontalHeaderLabels(["Job", "Progress", "Status"])

    @Slot(str)
    def reportError(self, err: str):
        LOG.error(err)

    @Slot(list)
    def startProcess(
        self, job_vars: tuple[str, dict[str, Any]], load_afterwards: bool = False
    ):
        log_queue = Queue()

        main_pipe, child_pipe = Pipe()
        pause_event = Event()
        entry_number = next(self.job_number)

        job_name, job_params = job_vars

        item_th = JobEntry(
            command=job_name,
            entry_number=entry_number,
            pause_event=pause_event,
            load_afterwards=load_afterwards,
        )
        item_th.handler.setFormatter(FMT)
        item_th.handler.setLevel("INFO")

        try:
            subprocess_ref = Subprocess(
                job_name=job_name,
                job_parameters=job_params,
                pipe=child_pipe,
                pause_event=pause_event,
                log_queue=log_queue,
            )
        except Exception as e:
            LOG.error(
                f"Failed to create Subprocess using {job_vars};\n"
                f"error {e};\n"
                f"traceback {traceback.format_exc()}"
            )
            return

        handlers = [item_th.handler] + LOG.handlers
        listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
        listener.start()

        communicator = JobCommunicator()
        watcher_thread = JobThread(communicator, main_pipe, subprocess_ref)
        communicator.moveToThread(watcher_thread)
        entry_number = next(self.job_number)
        item_th.parameters = job_params
        item_th.free_filename.connect(self.unprotect_filename)
        if load_afterwards:
            if job_name in Converter.subclasses():
                item_th.for_loading.connect(self.trajectory_for_loading)
            else:
                try:
                    int(job_params["output_files"][1])
                except Exception:
                    item_th.for_loading.connect(self.results_for_loading)
                else:
                    item_th.for_loading.connect(self.trajectory_for_loading)

        communicator.target.connect(item_th.on_started)  # int
        communicator.progress.connect(item_th.on_update)  # int
        communicator.finished.connect(item_th.on_finished)  # bool
        communicator.oscillate.connect(item_th.on_oscillate)  # nothing

        LOG.info("Watcher thread ready to start!")
        watcher_thread.start()
        try:
            task_name = str(job_name)
        except Exception:
            task_name = "This should have been a job name"

        name_item = QStandardItem(task_name)
        name_item.setData(entry_number, role=Qt.ItemDataRole.UserRole)
        self.protect_filename.emit(item_th.expected_output())
        self.appendRow(
            [
                name_item,
                item_th._prog_item,
                item_th._stat_item,
            ]
        )
        self.new_job_started.emit()
        # nrows = self.rowCount()
        # index = self.indexFromItem(item_th._item)
        # print(f"Index: {index}")
        self.jobs[entry_number] = Job(
            entry=item_th,
            process=subprocess_ref,
            thread=watcher_thread,
            listener=listener,
        )

        LOG.info("Subprocess ready to start!")
        subprocess_ref.start()

    def startProcessAndLoad(self, job_vars: list):
        self.startProcess(job_vars, load_afterwards=True)


class Job(NamedTuple):
    """Details of a job."""

    entry: JobEntry
    thread: JobThread
    process: Process
    listener: QueueListener
