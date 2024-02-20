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

from multiprocessing import Pipe, Queue, Process
from multiprocessing.connection import Connection

from icecream import ic

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Subprocess.JobStatusProcess import JobStatusProcess


class Subprocess(Process):
    def __init__(self, *args, **kwargs):
        super().__init__()
        job_name = kwargs.get("job_name")
        self._job_parameters = kwargs.get("job_parameters")
        sending_pipe = kwargs.get("pipe")
        receiving_queue = kwargs.get("queue")
        self.construct_job(job_name, sending_pipe, receiving_queue)
    
    def construct_job(self, job: str, pipe: Connection, queue: "Queue"):
        job_instance = IJob.create(job)
        job_instance.build_configuration()
        status = JobStatusProcess(pipe, queue)
        job_instance._status = status
        self._job_instance = job_instance
    
    def run(self):
        self._job_instance.run(self._job_parameters)
