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
from logging.handlers import QueueHandler
from multiprocessing import Event, Process, Queue
from multiprocessing.connection import Connection

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG
from MDANSE_GUI.Subprocess.JobStatusProcess import JobStatusProcess


class Subprocess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__()
        job_name = kwargs.get("job_name")
        self._job_parameters = kwargs.get("job_parameters")
        sending_pipe = kwargs.get("pipe")
        self.queue_0 = Queue()
        self.queue_1 = Queue()
        pause_event = kwargs.get("pause_event")
        self.log_queue = kwargs.get("log_queue")
        self.construct_job(
            job_name, sending_pipe, self.queue_0, self.queue_1, pause_event
        )

    def construct_job(
        self,
        job: str,
        pipe: Connection,
        queue_0: Queue,
        queue_1: Queue,
        pause_event: Event,
    ):
        job_instance = IJob.create(job)
        job_instance.build_configuration()
        status = JobStatusProcess(job, pipe, queue_0, queue_1, pause_event)
        job_instance._status = status
        self._job_instance = job_instance

    def run(self):
        queue_handler = QueueHandler(self.log_queue)
        LOG.addHandler(queue_handler)
        LOG.info("Running job")
        self._job_instance.run(self._job_parameters)
        LOG.removeHandler(queue_handler)

    def terminate(self):
        """Send out a terminate message to IJob so that it knows to
        terminate and join its subprocesses. We need to do this
        before this subprocess terminates itself.
        """
        if "running_mode" not in self._job_parameters:
            super().terminate()
            return

        if self._job_parameters["running_mode"][0] == "multicore":
            if self.queue_0.get() != "started":
                raise RuntimeError(
                    "For some reason we received a messaged which wasn't "
                    "'started' this is unexpected."
                )
            self.queue_1.put("terminate")
            # Wait until IJob has received the terminate message.
            while not self.queue_1.empty():
                time.sleep(0.1)
            if self.queue_0.get() != "terminated":
                raise RuntimeError(
                    "For some reason we received a messaged which wasn't "
                    "'terminated' this is unexpected."
                )
        super().terminate()
