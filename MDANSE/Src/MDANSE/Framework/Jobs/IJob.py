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
from __future__ import annotations

import abc
import multiprocessing
import os
import queue
import random
import stat
import string
import sys
import time
import traceback
from collections.abc import Sequence
from logging import FileHandler
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from pathlib import Path
from typing import Any

from more_itertools import consumer, first_true

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Jobs.JobStatus import JobStates, JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.MLogging import FMT, LOG

RUNSCRIPT = """\
#!{executable}

########################################################
# This is an automatically generated MDANSE run script #
########################################################

{import_line}

########################################################
# Job parameters                                       #
########################################################

parameters = {{
{param_str}
}}

########################################################
# Setup and run the analysis                           #
########################################################

if __name__ == "__main__":
    {var_name} = {parent}.create("{job_name}")
    # Progress bars only available if tqdm available.
    # Install with `cli` optional dependency.
    {var_name}.run(parameters, status=True, prog_bar=True)
"""


try:
    from tqdm import tqdm
except ImportError:
    LOG.debug("TQDM not installed, no progress bars")

    class tqdm:
        """Return dummy function for tqdm."""

        def __init__(self, x, *_args, **_kwargs):
            self.x = x

        def __iter__(self):
            return iter(self.x)

        def update(self, *_args, **_kwargs):
            pass


class JobError(Error):
    """This class handles any exception related to IJob-derived objects"""

    def __init__(self, job: IJob, message: str = ""):
        """
        Initializes the the object.

        Parameters
        ----------
        job : IJob
            The job in which the exception was raised.
        message : str
            Error report.
        """

        trace = [" -- ".join(map(str, tb)) for tb in traceback.extract_stack()]

        self._message = message
        trace.append(f"\n{self._message}")

        trace = "\n".join(trace)

        if job._status is not None:
            state = job._status.state
            state.state = JobStates.FAILED
            state.traceback = trace
            state.info = str(job)
            job._status.update(force=True)

    def __str__(self):
        return self._message


@consumer
def key_generator(
    keySize: int, chars: Sequence[str] = string.ascii_lowercase + string.digits
):
    prefix = ""

    while True:
        key = "".join(random.choices(chars, k=keySize))
        if prefix:
            key = f"{prefix}_{key}"

        new_prefix = yield key
        if new_prefix is not None:
            prefix = new_prefix


class IJob(Configurable, metaclass=SubclassFactory):
    """The parent class for any MDANSE job.

    Both analysis runs and converters inherit from IJob,
    but typically analysis runs are the only ones that can
    be run in parallel.
    """

    section = "job"
    key_gen = key_generator(6)
    ancestor = []
    runscript_import_line = "from MDANSE.Framework.Jobs.IJob import IJob"

    @classmethod
    def define_unique_name(cls):
        """
        Sets a name for the job that is not already in use by another running job.
        """

        cls.key_gen.send(f"{PLATFORM.username()[:4]}_{PLATFORM.pid():d}")

        # The list of the registered jobs.
        registeredJobs = {
            f.name for f in PLATFORM.temporary_files_directory().glob("*")
        }

        name = first_true(cls.key_gen, pred=lambda x: x not in registeredJobs)

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
        self._in_memory_result = None

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
        self._in_memory_result = getattr(self._outputData, "data_object", None)

    @property
    def results(self):
        return self._in_memory_result

    def initialize(self):
        try:
            if (
                "output_files" in self.configuration
                and self.configuration["output_files"]["write_logs"]
            ):
                log_filename = str(self.configuration["output_files"]["root"]) + ".log"
                self.add_log_file_handler(
                    log_filename, self.configuration["output_files"]["log_level"]
                )
        except KeyError:
            LOG.error("IJob did not find 'write_logs' in output_files")

        if selection := self.configuration.get("atom_selection"):
            try:
                array_length = selection["total_number_of_atoms"]
            except KeyError:
                LOG.warning(
                    "Job could not find total number of atoms in atom selection."
                )
            else:
                valid_indices = selection["flatten_indices"]
                self._outputData.add(
                    "selected_atoms",
                    "LineOutputVariable",
                    [index in valid_indices for index in range(array_length)],
                )
        self.set_up_trajectory()

    def set_up_trajectory(self):
        """Apply operations to the trajectory instance, if present.

        Atom selection, atom transmutation and result grouping are all
        applied to the Trajectory object. If the job works on a trajectory,
        the Trajectory instance is now saved as an attribute of this IJob
        instance.

        These operations were previously handled by IConfigurator subclasses.
        """
        if (trajectory := self.configuration.get("trajectory")) is None:
            return
        self.trajectory = trajectory["instance"]
        if (selection := self.configuration.get("atom_selection")) is not None:
            self.trajectory.set_selection(selection["flatten_indices"])
        if (transmutation := self.configuration.get("atom_transmutation")) is not None:
            self.trajectory.set_transmutation(transmutation.transmutation)
        if (grouping := self.configuration.get("grouping_level")) is not None:
            self.trajectory.set_grouping(grouping["level"])

    @abc.abstractmethod
    def run_step(self, index):
        pass

    def preview_output_axis(self):
        axes = {}
        for configurator in self._configuration.values():
            preview_method = getattr(configurator, "preview_output_axis", None)
            if callable(preview_method):
                axis, unit = preview_method()
                if axis is not None:
                    axes[unit] = axis
        return axes

    @classmethod
    def save(
        cls, jobFile: Path | str, parameters: dict[str, Any] | None = None
    ) -> None:
        """Save a job file for a given job.

        Parameters
        ----------
        jobFile : Path
            The name of the output job file.
        parameters : Optional[dict[str, Any]]
            If not None, the parameters with which the job file will be built.
        """
        if parameters is None:
            parameters = cls.get_default_parameters()

        parameters = {
            key: (val, label) if not isinstance(val, Path) else (str(val), label)
            for key, (val, label) in sorted(parameters.items())
        }

        param_str = "\n".join(
            f"    {k!r}: {v!r}," + ("# " + label if label else "")
            for k, (v, label) in parameters.items()
        )

        with open(jobFile, "w") as f:
            f.write(
                RUNSCRIPT.format(
                    executable=sys.executable,
                    import_line=cls.runscript_import_line,
                    param_str=param_str,
                    parent=cls.runscript_import_line.split(" ")[-1],
                    var_name=cls.__name__.lower(),
                    job_name=cls.__name__,
                )
            )

        os.chmod(jobFile, stat.S_IRWXU)

    def combine(self):
        if self._status is not None:
            if self._status.is_stopped():
                self._status.cleanup()
            else:
                self._status.update()

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
                    self.trajectory.close()
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

    def _run_singlecore(self, *, prog: bool = False):
        LOG.info(f"Single-core run: expects {self.numberOfSteps} steps")

        steps = range(self.numberOfSteps)
        if prog:
            steps = tqdm(
                steps, unit="steps", total=self.numberOfSteps, desc=type(self).__name__
            )

        for index in steps:
            if self._status is not None:
                if hasattr(self._status, "_pause_event"):
                    self._status._pause_event.wait()

            idx, result = self.run_step(index)
            if self._status is not None:
                self._status.update()

            self.combine(idx, result)
        LOG.info("Single-core job completed all the steps")

    def _run_multicore(self, *, prog: bool = False):
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

        steps = range(self.numberOfSteps + 1)
        if prog:
            steps = tqdm(
                steps, total=self.numberOfSteps, unit="steps", desc=type(self).__name__
            )
        steps = iter(steps)

        n_results = next(steps)
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
                n_results = next(steps)
                self.combine(index, result)

        if self._status is not None:
            self._status.fixed_status(n_results)

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

    def _run_remote(self, *, prog: bool = False):
        raise NotImplementedError(
            "Currently there is no replacement for the old Pyro remote runs."
        )

    _runner = {
        "single-core": _run_singlecore,
        "multicore": _run_multicore,
        "remote": _run_remote,
    }

    def run(self, parameters, status: bool = False, prog_bar: bool = False):
        """
        Run the job.
        """
        if isinstance(self._status, JobStatus) and hasattr(self._status, "state"):
            raise RuntimeError(
                f"Unable to run an instance of job with name {self._name} more than once."
            )

        try:
            self._name = f"{type(self).__name__}_{IJob.define_unique_name()}"

            if status and self._status is None:
                self._status = self._status_constructor(self)

            self.setup(parameters)

            self.initialize()

            self.check_status()

            if self._status is not None:
                self._status.start(self.numberOfSteps)
                self._status.state.info = str(self)

            if getattr(self, "numberOfSteps", 0) <= 0:
                raise JobError(self, f"Invalid number of steps for job {self._name}")

            if "running_mode" in self.configuration:
                mode = self.configuration["running_mode"]["mode"]
            else:
                mode = "single-core"

            IJob._runner[mode](self, prog=prog_bar)

            self.finalize()

            if self._status is not None:
                self._status.finish()
        except Exception as err:
            tb = traceback.format_exc()
            LOG.critical(f"Job failed with traceback: {tb}")
            raise JobError(self) from err

    @property
    def info(self) -> str:
        return (
            self.__doc__
            + "\nInput Parameters\n================\n"
            + "\n".join(
                sorted(f"{key}: {value}" for key, value in self.settings.items())
            )
        )

    @classmethod
    def save_template(cls, shortname, classname):
        if shortname in IJob.subclasses():
            raise KeyError(
                f"A job with {shortname!r} name is already stored in the registry"
            )

        templateFile = PLATFORM.macros_directory() / f"{classname}.py"

        try:
            label = "label of the class"
            with templateFile.open("w") as f:
                f.write(
                    f'''import collections

from MDANSE.Framework.Jobs.IJob import IJob

class {classname}(IJob):
    """
    You should enter the description of your job here ...
    """

    # You should enter the label under which your job will be viewed from the gui.
    label = {label!r}

    # You should enter the category under which your job will be references.
    category = ('My jobs',)

    # You should enter the configuration of your job here
    # Here a basic example of a job that will use a HDF trajectory, a frame selection and an output file in HDF5 and Text file formats
    settings = collections.OrderedDict()
    settings['trajectory']=('hdf_trajectory',{{}})
    settings['frames']=('frames', {{"dependencies":{{'trajectory':'trajectory'}}}})
    settings['output_files']=('output_files', {{"formats":["HDFFormat","netcdf","TextFormat"]}})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # Compulsory. You must enter the number of steps of your job.
        # Here for example the number of selected frames
        self.numberOfSteps = self.configuration['frames']['number']

        # Create an output data for the selected frames.
        self._outputData.add("x/axes/time", "LineOutputVariable", self.configuration['frames']['time'], units='ps')


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
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], str(self),
            self.output_configuration())

        # The trajectory is closed
        self.configuration['trajectory']['instance'].close()

'''
                )

        except OSError:
            return None
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
        PLATFORM.create_directory(Path(self._log_filename).parent)
        fh = FileHandler(self._log_filename, mode="w")
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
