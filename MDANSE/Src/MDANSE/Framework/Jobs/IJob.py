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
from multiprocessing import Queue
from logging import FileHandler
from logging.handlers import QueueHandler, QueueListener

import abc
import glob
import os
import multiprocessing
import queue
import random
import stat
import string
import time
import sys
import traceback

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Jobs.JobStatus import JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.MLogging import LOG, FMT


class JobError(Error):
    """
    This class handles any exception related to IJob-derived objects
    """

    def __init__(self, job, message=None):
        """
        Initializes the the object.

        :param job: the configurator in which the exception was raised
        :type job: IJob derived object
        """

        trace = []

        tback = traceback.extract_stack()

        for tb in tback:
            trace.append(" -- ".join([str(t) for t in tb]))

        if message is None:
            message = sys.exc_info()[1]

        self._message = str(message)

        trace.append("\n%s" % self._message)

        trace = "\n".join(trace)

        if job._status is not None:
            job._status._state["state"] = "aborted"
            job._status._state["traceback"] = trace
            job._status._state["info"] = str(job)
            job._status.update(force=True)

    def __str__(self):
        return self._message


def key_generator(keySize, chars=None, prefix=""):
    if chars is None:
        chars = string.ascii_lowercase + string.digits

    key = "".join(random.choice(chars) for _ in range(keySize))
    if prefix:
        key = "%s_%s" % (prefix, key)

    return key


class IJob(Configurable, metaclass=SubclassFactory):
    """
    This class handles a MDANSE job. In MDANSE any task modeled by a loop can be considered as a MDANSE job.
    """

    section = "job"

    ancestor = []

    @staticmethod
    def define_unique_name():
        """
        Sets a name for the job that is not already in use by another running job.
        """

        prefix = "%s_%d" % (PLATFORM.username()[:4], PLATFORM.pid())

        # The list of the registered jobs.
        registeredJobs = [
            os.path.basename(f)
            for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(), "*"))
        ]

        while True:
            # Followed by 4 random letters.
            name = key_generator(6, prefix=prefix)

            if not name in registeredJobs:
                break

        return name

    def __init__(self, trajectory_input="mdanse"):
        """
        The base class constructor.
        """

        Configurable.__init__(self, trajectory_input=trajectory_input)

        self._outputData = OutputData()

        self._status_constructor = JobStatus

        self._status = None

        self._processes = []

        self._log_filename = None

        self.inputQueue = Queue()
        self.outputQueue = Queue()
        self.log_queue = Queue()

    def __getstate__(self):
        d = self.__dict__.copy()
        del d["_processes"]
        return d

    @property
    def name(self):
        return self._name

    @property
    def configuration(self):
        return self._configuration

    def finalize(self):
        if self._log_filename is not None:
            self.remove_log_file_handler()

    def initialize(self):
        try:
            if (
                "output_files" in self.configuration
                and self.configuration["output_files"]["write_logs"]
            ):
                log_filename = self.configuration["output_files"]["root"] + ".log"
                self.add_log_file_handler(
                    log_filename, self.configuration["output_files"]["log_level"]
                )
        except KeyError:
            LOG.error("IJob did not find 'write_logs' in output_files")

    @abc.abstractmethod
    def run_step(self, index):
        pass

    def preview_output_axis(self):
        axes = {}
        for configurator in self._configuration.values():
            axis, unit = configurator.preview_output_axis()
            if axis is None:
                continue
            axes[unit] = axis
        return axes

    @classmethod
    def save(cls, jobFile, parameters=None):
        """
        Save a job file for a given job.\n
        :Parameters:
            #. jobFile (str): The name of the output job file.\n
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """

        f = open(jobFile, "w")

        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write("#!%s\n\n" % sys.executable)

        # Writes the input file header.
        f.write("########################################################\n")
        f.write("# This is an automatically generated MDANSE run script #\n")
        f.write("########################################################\n\n")

        # Write the import.
        f.write("from MDANSE.Framework.Jobs.IJob import IJob\n\n")

        f.write("########################################################\n")
        f.write("# Job parameters                                       #\n")
        f.write("########################################################\n\n")

        # Writes the line that will initialize the |parameters| dictionary.
        if parameters is None:
            parameters = cls.get_default_parameters()

        f.write("parameters = {\n")
        for k, (v, label) in sorted(parameters.items()):
            if label:
                f.write(f"    {repr(k) + ': ' + repr(v) + ',':<50}  # {label}\n")
            else:
                f.write(f"    {repr(k) + ': ' + repr(v) + ',':<50}\n")
        f.write("}\n")

        f.write("\n")
        f.write("########################################################\n")
        f.write("# Setup and run the analysis                           #\n")
        f.write("########################################################\n")
        f.write("\n")

        f.write('if __name__ == "__main__":\n')
        f.write("    %s = IJob.create(%r)\n" % (cls.__name__.lower(), cls.__name__))
        f.write("    %s.run(parameters, status=True)\n" % (cls.__name__.lower()))

        f.close()

        os.chmod(jobFile, stat.S_IRWXU)

    def combine(self):
        if self._status is not None:
            if self._status.is_stopped():
                self._status.cleanup()
            else:
                self._status.update()

    def _run_singlecore(self):
        LOG.info(f"Single-core run: expects {self.numberOfSteps} steps")
        for index in range(self.numberOfSteps):
            if self._status is not None:
                if hasattr(self._status, "_pause_event"):
                    self._status._pause_event.wait()
            idx, result = self.run_step(index)
            if self._status is not None:
                self._status.update()
            self.combine(idx, result)
        LOG.info("Single-core job completed all the steps")

    def process_tasks_queue(self, tasks, outputs, log_queues):

        queue_handlers = []
        for log_queue in log_queues:
            queue_handler = QueueHandler(log_queue)
            queue_handlers.append(queue_handler)
            LOG.addHandler(queue_handler)

        while True:
            try:
                index = tasks.get_nowait()
            except queue.Empty:
                if tasks.empty():
                    self.configuration["trajectory"]["instance"].close()
                    break
            else:
                if self._status is not None:
                    if hasattr(self._status, "_pause_event"):
                        self._status._pause_event.wait()
                output = self.run_step(index)
                outputs.put(output)

        for queue_handler in queue_handlers:
            LOG.removeHandler(queue_handler)

        return True

    def _run_multicore(self):
        if hasattr(self._status, "_queue_0"):
            self._status._queue_0.put("started")

        inputQueue = self.inputQueue
        outputQueue = self.outputQueue
        log_queue = self.log_queue

        log_queues = [log_queue]
        handlers = []  # handlers that are not QueueHandlers
        for handler in LOG.handlers:
            if isinstance(handler, QueueHandler):
                log_queues.append(handler.queue)
            else:
                handlers.append(handler)

        listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
        listener.start()

        self._processes = []

        for i in range(self.numberOfSteps):
            inputQueue.put(i)

        for i in range(self.configuration["running_mode"]["slots"]):
            self._run_multicore_check_terminate(listener)
            p = multiprocessing.Process(
                target=self.process_tasks_queue,
                args=(inputQueue, outputQueue, log_queues),
            )
            self._processes.append(p)
            p.daemon = False
            p.start()

        n_results = 0
        while n_results != self.numberOfSteps:
            self._run_multicore_check_terminate(listener)
            if self._status is not None:
                self._status.fixed_status(n_results)
            try:
                index, result = outputQueue.get_nowait()
            except queue.Empty:
                time.sleep(0.1)
                continue
            else:
                n_results += 1
                self.combine(index, result)

        for p in self._processes:
            p.join()

        LOG.info("Multicore job finished: all subprocesses ended.")

        for p in self._processes:
            p.close()

        listener.stop()

    def _run_multicore_check_terminate(self, listener) -> None:
        """Check if a terminate job was added to the queue. If it was
        added we need to terminate and join all child processes.

        Parameters
        ----------
        listener : QueueListener
            The log listener that we need to stop.
        """
        if not (
            hasattr(self._status, "_queue_0") and hasattr(self._status, "_queue_1")
        ):
            return
        if not self._status._queue_1.empty():
            if self._status._queue_1.get() == "terminate":
                LOG.warning("Job received a request to terminate. Aborting the run.")
                for p in self._processes:
                    p.terminate()
                    p.join()
                listener.stop()
                self._status._queue_0.put("terminated")
                # we've terminated the child processes, now we wait
                # here as the whole subprocess will be terminated.
                # We don't want IJob doing anything else from now
                # onwards.
                while True:
                    time.sleep(10)

    def _run_remote(self):
        raise NotImplementedError(
            "Currently there is no replacement for the old Pyro remote runs."
        )

    _runner = {
        "single-core": _run_singlecore,
        "multicore": _run_multicore,
        "remote": _run_remote,
    }

    def run(self, parameters, status=False):
        """
        Run the job.
        """

        try:
            self._name = "%s_%s" % (self.__class__.__name__, IJob.define_unique_name())

            if status and self._status is None:
                self._status = self._status_constructor(self)

            self.setup(parameters)

            self.initialize()

            if self._status is not None:
                self._status.start(self.numberOfSteps)
                self._status.state["info"] = str(self)

            if getattr(self, "numberOfSteps", 0) <= 0:
                raise JobError(self, "Invalid number of steps for job %s" % self._name)

            if "running_mode" in self.configuration:
                mode = self.configuration["running_mode"]["mode"]
            else:
                mode = "single-core"

            IJob._runner[mode](self)

            self.finalize()

            if self._status is not None:
                self._status.finish()
        except:
            tb = traceback.format_exc()
            LOG.critical(f"Job failed with traceback: {tb}")
            raise JobError(self, tb)

    @property
    def info(self):
        return self._info

    @classmethod
    def save_template(cls, shortname, classname):
        if shortname in IJob.subclasses():
            raise KeyError(
                "A job with %r name is already stored in the registry" % shortname
            )

        templateFile = os.path.join(PLATFORM.macros_directory(), "%s.py" % classname)

        try:
            f = open(templateFile, "w")

            f.write(
                '''import collections

from MDANSE.Framework.Jobs.IJob import IJob

class %(classname)s(IJob):
    """
    You should enter the description of your job here ...
    """
        
    # You should enter the label under which your job will be viewed from the gui.
    label = %(label)r

    # You should enter the category under which your job will be references.
    category = ('My jobs',)
    
    ancestor = ["hdf_trajectory"]

    # You should enter the configuration of your job here
    # Here a basic example of a job that will use a HDF trajectory, a frame selection and an output file in HDF5 and Text file formats
    settings = collections.OrderedDict()
    settings['trajectory']=('hdf_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['output_files']=('output_files', {"formats":["HDFFormat","netcdf","TextFormat"]})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # Compulsory. You must enter the number of steps of your job.
        # Here for example the number of selected frames
        self.numberOfSteps = self.configuration['frames']['number']
                        
        # Create an output data for the selected frames.
        self._outputData.add("time", "LineOutputVariable", self.configuration['frames']['time'], units='ps')


    def run_step(self, index):
        """
        Runs a single step of the job.
        """
                                
        return index, None
    
    
    def combine(self, index, x):
        """
        Synchronize the output of each individual run_step output.
        """     
                    
    def finalize(self):
        """
        Finalizes the job (e.g. averaging the total term, output files creations ...).
        """ 

        # The output data are written
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info,
            self.output_configuration())
        
        # The trajectory is closed
        self.configuration['trajectory']['instance'].close()        

'''
                % {
                    "classname": classname,
                    "label": "label of the class",
                    "shortname": shortname,
                }
            )

        except IOError:
            return None
        else:
            f.close()
            return templateFile

    def add_log_file_handler(self, filename: str, level: str) -> None:
        """Adds a file handle which is used to write the jobs logs.

        Parameters
        ----------
        filename : str
            The log's filename.
        level : str
            The log level.
        """
        self._log_filename = filename
        fh = FileHandler(filename, mode="w")
        # set the name so that we can track it and then close it later,
        # tracking the fh by storing it in this object causes issues
        # with multiprocessing jobs
        fh.set_name(filename)
        fh.setFormatter(FMT)
        fh.setLevel(level)
        LOG.addHandler(fh)
        LOG.debug(f"Log handler added for filename {filename}")

    def remove_log_file_handler(self) -> None:
        """Removes the IJob file handle from the MDANSE logger."""
        LOG.debug("Disconnecting log handlers")
        for handler in LOG.handlers:
            if handler.name == self._log_filename:
                handler.close()
                LOG.removeHandler(handler)
