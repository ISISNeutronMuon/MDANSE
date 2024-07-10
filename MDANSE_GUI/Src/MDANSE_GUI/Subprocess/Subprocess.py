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
from logging.handlers import QueueHandler
from multiprocessing import Queue, Process, Event
from multiprocessing.connection import Connection

from MDANSE.MLogging import LOG
from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Subprocess.JobStatusProcess import JobStatusProcess


class Subprocess(Process):

    def __init__(self, *args, **kwargs):
        super().__init__()
        job_name = kwargs.get("job_name")
        self._job_parameters = kwargs.get("job_parameters")
        sending_pipe = kwargs.get("pipe")
        receiving_queue = kwargs.get("queue")
        pause_event = kwargs.get("pause_event")
        self.log_queue = kwargs.get("log_queue")
        self.construct_job(job_name, sending_pipe, receiving_queue, pause_event)

    def construct_job(
        self, job: str, pipe: Connection, queue: "Queue", pause_event: "Event"
    ):
        job_instance = IJob.create(job)
        job_instance.build_configuration()
        status = JobStatusProcess(pipe, queue, pause_event)
        job_instance._status = status
        self._job_instance = job_instance

    def run(self):
        queue_handler = QueueHandler(self.log_queue)
        LOG.addHandler(queue_handler)
        LOG.info("Running job")
        self._job_instance.run(self._job_parameters)
        LOG.removeHandler(queue_handler)
