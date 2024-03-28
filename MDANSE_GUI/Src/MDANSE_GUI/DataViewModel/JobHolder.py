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

from icecream import ic

from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QObject, Slot, Signal, QProcess, QThread, QMutex

from MDANSE_GUI.DataViewModel.JobStatusQt import JobStatusQt


class JobThread(QThread):
    """A wrapper object for a single MDANSE analysis job.
    It is created to run a single instance of the job,
    and exits once the job has completed processing."""

    job_failure = Signal(str)

    def __init__(self, *args, command=None, parameters={}):
        super().__init__(*args)
        ic("JobThread starts init")
        self._command = command
        self._parameters = parameters
        ic(f"JobThread.run will create a job instance of command {command}")
        if isinstance(self._command, type):
            self._job = self._command()
        else:
            self._job = self._command
        self._job.build_configuration()
        ic(f"JobThread._parameters: {self._parameters}")
        # here we try to create and connect a JobStatusQt
        status = JobStatusQt(parent=self)
        self._job._status = status
        self._status = status
        ic("JobThread finished init")

    def run(self):
        try:
            self._job.run(self._parameters)
        except Exception as inst:
            ic("JobThread has entered exception handling!")
            error_message = ""
            error_message += str(type(inst))
            error_message += str(inst.args)  # arguments stored in .args
            error_message += str(inst)  # __str__ allows args to be printed directly,
            ic("JobThread is about to emit the failure message")
            self.job_failure.emit(error_message)
        else:
            ic("JobThread.run did not raise an exception. JobThread.run will exit now")
        self.exec()  # this starts event handling - will it help?


class JobEntry(QObject):
    """This coordinates all the objects that make up one line on the list
    of current jobs. It is used for reporting the task progress to the GUI."""

    def __init__(self, *args, command=None):
        super().__init__(*args)
        self._command = command
        self._parameters = {}
        self.has_started = False
        self.has_finished = False
        self.success = None
        self.percent_complete = 0
        self._output = None
        self.reference = None
        self.total_steps = 99
        self._prog_item = QStandardItem()
        self._stat_item = QStandardItem()

    @property
    def parameters(self):
        return self._parameters

    @parameters.setter
    def set_parameters(self, input: dict):
        self._parameters = input

    def update_fields(self):
        self._prog_item.setText(f"{self.percent_complete} percent complete")

    @Slot(bool)
    def on_finished(self, success: bool):
        print("Item received on_finished!")
        self.success = success
        self.has_finished = True
        self._stat_item.setText("Stopped")
        if success:
            self.percent_complete = 100
            self._stat_item.setText("Completed!")
        self.update_fields()

    @Slot(int)
    def on_started(self, target_steps: int):
        print("Item received on_started!")
        self.total_steps = target_steps
        self.has_started = True
        self._stat_item.setText("Starting")
        self.update_fields()

    @Slot(int)
    def on_update(self, completed_steps: int):
        print("Item received on_update!")
        self.percent_complete = completed_steps / self.total_steps * 99
        self._stat_item.setText("Running")
        self.update_fields()

    @Slot()
    def on_oscillate(self):
        """For jobs with unknown duration, the progress bar will bounce."""


class JobHolder(QStandardItemModel):
    """All the job INSTANCES that are started by the GUI
    are added to this model."""

    def __init__(self, parent: QObject = None):
        super().__init__(parent=parent)
        self.lock = QMutex()
        self.existing_threads = []
        self.existing_jobs = []

    @Slot(str)
    def reportError(self, err: str):
        ic(err)

    @Slot(object)
    def addItem(self, new_entry: QProcess):
        traj = JobEntry(new_entry.basename, trajectory=new_entry)
        self.appendRow([traj])

    @Slot(list)
    def startThread(self, job_vars: list):
        try:
            th_ref = JobThread(command=job_vars[0], parameters=job_vars[1])
        except:
            ic(f"Failed to create JobThread using {job_vars}")
            return
        th_ref.job_failure.connect(self.reportError)
        item_th = JobEntry(command=job_vars[0])
        th_ref._status._communicator.target.connect(item_th.on_started)  # int
        th_ref._status._communicator.progress.connect(item_th.on_update)  # int
        th_ref._status._communicator.finished.connect(item_th.on_finished)  # bool
        th_ref._status._communicator.oscillate.connect(item_th.on_oscillate)  # nothing
        ic("Thread ready to start!")
        try:
            task_name = str(job_vars[0].__name__)
        except AttributeError:
            task_name = str(job_vars[0].__class__.__name__)
        self.appendRow(
            [
                QStandardItem(task_name),
                item_th._prog_item,
                item_th._stat_item,
            ]
        )
        # nrows = self.rowCount()
        # index = self.indexFromItem(item_th._item)
        # print(f"Index: {index}")
        th_ref.start()
        self.existing_threads.append(th_ref)
        self.existing_jobs.append(item_th)
