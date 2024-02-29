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

from multiprocessing import Pipe, Queue, Event

from icecream import ic

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QProcess, QThread, QMutex, Qt

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


class JobThread(QThread):

    def __init__(self, job_comm: "JobCommunicator", receiving_end: "Connection"):
        super().__init__()
        self._job_comm = job_comm
        self._pipe_end = receiving_end
        self._keep_running = True

    def run(self):
        while self._keep_running:
            try:
                status_update = self._pipe_end.recv()
            except:
                self._job_comm.status_update(("COMMUNICATION", False))
                self._keep_running = False
            else:
                self._job_comm.status_update(status_update)


class JobEntry(QObject):
    """This coordinates all the objects that make up one line on the list
    of current jobs. It is used for reporting the task progress to the GUI."""

    def __init__(self, *args, command=None, entry_number=0, pause_event=None):
        super().__init__(*args)
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
        self.percent_complete = round(99 * completed_steps / self.total_steps, 1)
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


class JobHolder(QStandardItemModel):
    """All the job INSTANCES that are started by the GUI
    are added to this model."""

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.lock = QMutex()
        self.existing_threads = {}
        self.existing_processes = {}
        self.existing_jobs = {}
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
        main_pipe, child_pipe = Pipe()
        main_queue = Queue()
        pause_event = Event()
        try:
            subprocess_ref = Subprocess(
                job_name=job_vars[0],
                job_parameters=job_vars[1],
                pipe=child_pipe,
                queue=main_queue,
                pause_event=pause_event,
            )
        except:
            ic(f"Failed to create Subprocess using {job_vars}")
            return
        communicator = JobCommunicator()
        watcher_thread = JobThread(communicator, main_pipe)
        communicator.moveToThread(watcher_thread)
        entry_number = self.next_number
        item_th = JobEntry(
            command=job_vars[0], entry_number=entry_number, pause_event=pause_event
        )
        item_th.parameters = job_vars[1]
        communicator.target.connect(item_th.on_started)  # int
        communicator.progress.connect(item_th.on_update)  # int
        communicator.finished.connect(item_th.on_finished)  # bool
        communicator.oscillate.connect(item_th.on_oscillate)  # nothing
        ic("Watcher thread ready to start!")
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
        ic("Subprocess ready to start!")
        subprocess_ref.start()
