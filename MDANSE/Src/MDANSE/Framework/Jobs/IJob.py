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
import json
import pprint
import queue
import random
import stat
import string
import sys
import time
import traceback
from logging import FileHandler
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Process, Queue
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from more_itertools import consumer, first_true

from MDANSE import PLATFORM
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Jobs.JobStatus import JobStates, JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Framework.Parameters.Parameters import Configurable, DescID
from MDANSE.MLogging import FMT, LOG, LogLevels

if TYPE_CHECKING:
    from collections.abc import Sequence

    from MDANSE.Framework.Parameters import PredictionResult

if TYPE_CHECKING:
    from collections.abc import Sequence


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


RUNSCRIPT = """\
#!{executable}

import os
os.environ.update(
    OMP_NUM_THREADS = '1',
    OPENBLAS_NUM_THREADS = '1',
    MKL_NUM_THREADS = '1',
    VECLIB_MAXIMUM_THREADS = '1',
    NUMEXPR_NUM_THREADS = '1'
)

########################################################
# This is an automatically generated MDANSE run script #
########################################################

{import_line}

########################################################
# Job parameters                                       #
########################################################

parameters = {{
{param_str}}}

########################################################
# Setup and run the analysis                           #
########################################################

if __name__ == "__main__":
    {var_name} = {parent}.create("{job_name}")
    # Progress bars only available if tqdm available.
    # Install with `cli` optional dependency.
    {var_name}.run(parameters, status=True, prog_bar=True)
"""


class JobError(Exception):
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


def _format_params(parameters: dict) -> str:
    """Format the job parameters.

    Parameters
    ----------
    parameters : dict
        The jobs parameter dictionary.

    Returns
    -------
    str
        A formatted string of parameter used in the runscripts.
    """
    param_str = ""
    for k, v in parameters.items():
        str_v = str(v)
        if (
            isinstance(v, str)
            and len(str_v) > 72
            and str_v.startswith("{")
            and str_v.endswith("}")
        ):
            # if it's a long json string then try to make a multiline
            # string and format it
            try:
                json_data = json.loads(str_v)
                param = f'"""{json.dumps(json_data, indent=4)}"""'
                param = param.replace("\n", "\n    ")
            except json.decoder.JSONDecodeError:
                param = repr(v)
        elif isinstance(v, (tuple, list, dict)):
            param = pprint.pformat(v, indent=0, width=72)
            param = param.replace("\n", "\n        ")
        else:
            param = repr(v)
        param_str += f"    {k!r}: {param},  \n"
    return param_str


class IJob(Configurable, metaclass=SubclassFactory):
    """The parent class for any MDANSE job.

    Both analysis runs and converters inherit from IJob,
    but typically analysis runs are the only ones that can
    be run in parallel.
    """

    section = "job"
    key_gen = key_generator(6)
    ancestor: ClassVar[list[str]] = []
    PREDICTORS: ClassVar[tuple[DescID, ...]] = ()
    runscript_import_line = "from MDANSE.Framework.Jobs.IJob import IJob"

    enabled = True

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

    def __init__(self):
        """
        The base class constructor.
        """

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
        d = self.__dict__.copy() | super().__getstate__()
        # Remove hidden internals
        to_remove = tuple(map("_".__add__, self.parameters))
        d = {key: value for key, value in d.items() if not key.startswith(to_remove)}
        del d["_processes"]
        return d

    @property
    def name(self):
        return self._name

    def finalize(self):
        if self._log_filename is not None:
            self.remove_log_file_handler()
        self._in_memory_result = getattr(self._outputData, "data_object", None)

    @property
    def results(self):
        return self._in_memory_result

    def initialize(self):
        if hasattr(self, "output_files"):
            if self.output_files.write_logs:
                log_filename = self.output_files.path.with_suffix(".log")
                self.add_log_file_handler(log_filename, self.output_files.log_level)
        else:
            LOG.error("IJob did not find 'write_logs' in output_files")

        if selection := getattr(self, "atom_selection", None):
            try:
                array_length = self.trajectory.get_total_natoms(total=True)
            except KeyError:
                LOG.warning(
                    "Job could not find total number of atoms in atom selection."
                )
            else:
                valid_indices = selection
                self._outputData.add(
                    "selected_atoms",
                    "LineOutputVariable",
                    [index in valid_indices for index in range(array_length)],
                )

    @abc.abstractmethod
    def run_step(self, index):
        pass

    def preview_output_axis(self) -> list[PredictionResult]:
        """Collect the output axis values and unit information from parameters.

        Returns
        -------
        dict[str, Sequence[float]]
            Dictionary of {unit: values} pairs, predicting the data output range.
        """
        axes = []
        config = self.configuration
        raw_values = self.raw_values
        descriptors = self.descriptors
        for predictor in self.PREDICTORS:
            desc, val, raw = (
                descriptors[predictor],
                config[predictor],
                raw_values[predictor],
            )

            for prediction in desc.preview_output_axis(val, raw):
                if prediction is not None:
                    axes.append(prediction)
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
        parameters : dict[str, Any], optional
            If not None, the parameters with which the job file will be built.
        """
        if parameters is None:
            parameters = cls._get_default_parameters()

        jobFile = Path(jobFile)

        parameters = {
            key: val if not isinstance(val, Path) else str(val)
            for key, val in parameters.items()
        }

        with open(jobFile, "w") as f:
            f.write(
                RUNSCRIPT.format(
                    executable=sys.executable,
                    import_line=cls.runscript_import_line,
                    param_str=_format_params(parameters),
                    parent=cls.runscript_import_line.split(" ")[-1],
                    var_name=cls.__name__.lower(),
                    job_name=cls.__name__,
                )
            )

        jobFile.chmod(stat.S_IRWXU)

    def combine(self, index: int, x: Any) -> Any:
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

        for _ in range(self.running_mode.n_procs):
            self._run_multicore_check_terminate(listener)
            p = Process(
                target=self.process_tasks_queue,
                args=(inputQueue, outputQueue, log_queues),
            )
            self._processes.append(p)
            p.daemon = False
            p.start()

        steps = range(self.numberOfSteps + 1)
        if prog:
            steps = tqdm(
                steps,
                total=self.numberOfSteps,
                unit="steps",
                desc=type(self).__name__,
            )
        steps = iter(steps)

        n_results = next(steps)
        while n_results < self.numberOfSteps:
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
        if (
            not self._status._queue_1.empty()
            and self._status._queue_1.get() == "terminate"
        ):
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

    def run(
        self,
        parameters: dict[str, Any] | None = None,
        status: bool = False,
        prog_bar: bool = False,
    ):
        """
        Run the job.
        """
        if parameters is None:
            parameters = {}

        if isinstance(self._status, JobStatus) and hasattr(self._status, "state"):
            raise RuntimeError(
                f"Unable to run an instance of job with name {self._name} more than once."
            )

        if parameters is None:
            parameters = {}

        try:
            self._name = f"{type(self).__name__}"

            if status and self._status is None:
                self._status = self._status_constructor(self)

            self.configuration = parameters

            self.initialize()

            if self._status is not None:
                self._status.start(self.numberOfSteps)
                self._status.state.info = str(self)

            if getattr(self, "numberOfSteps", 0) <= 0:
                raise JobError(self, f"Invalid number of steps for job {self._name}")

            if "running_mode" in self.parameters:
                mode = self.running_mode.mode
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

    def add_log_file_handler(self, filename: Path, level: LogLevels) -> None:
        """Adds a file handle which is used to write the jobs logs.

        Parameters
        ----------
        filename : str
            The log's filename.
        level : str
            The log level.
        """
        self._log_filename = filename
        PLATFORM.create_directory(self._log_filename.parent)
        fh = FileHandler(self._log_filename, mode="w")
        # set the name so that we can track it and then close it later,
        # tracking the fh by storing it in this object causes issues
        # with multiprocessing jobs
        fh.set_name(str(filename))
        fh.setFormatter(FMT)
        fh.setLevel(level.value)
        LOG.addHandler(fh)
        LOG.debug(f"Log handler added for {filename}.")

    def remove_log_file_handler(self) -> None:
        """Removes the IJob file handle from the MDANSE logger."""
        LOG.debug("Disconnecting log handlers")
        for handler in LOG.handlers:
            if handler.name == str(self._log_filename):
                handler.close()
                LOG.removeHandler(handler)
