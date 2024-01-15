# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/IJob.py
# @brief     Implements module/class/test IJob
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
import glob
import os
import multiprocessing
import queue
import random
import stat
import string
import subprocess
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor as PoolExecutor

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Jobs.JobStatus import JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData

from MDANSE.Core.SubclassFactory import SubclassFactory


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

    def __init__(self):
        """
        The base class constructor.
        """

        Configurable.__init__(self)

        self._outputData = OutputData()

        self._status_constructor = JobStatus

        self._status = None

    @property
    def name(self):
        return self._name

    @property
    def configuration(self):
        return self._configuration

    @abc.abstractmethod
    def finalize(self):
        pass

    @abc.abstractmethod
    def initialize(self):
        pass

    @abc.abstractmethod
    def run_step(self, index):
        pass

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

        f.write("################################################################\n")
        f.write("# Job parameters                                               #\n")
        f.write("################################################################\n\n")

        # Writes the line that will initialize the |parameters| dictionary.
        f.write("parameters = {}\n")

        if parameters is None:
            parameters = cls.get_default_parameters()

        for k, v in sorted(parameters.items()):
            f.write("parameters[%r] = %r\n" % (k, v))

        f.write("\n")
        f.write("################################################################\n")
        f.write("# Setup and run the analysis                                   #\n")
        f.write("################################################################\n")
        f.write("\n")

        f.write('if __name__ == "__main__":\n')
        f.write("    %s = IJob.create(%r)\n" % (cls._type, cls.__name__))
        f.write("    %s.run(parameters,status=True)" % (cls._type))

        f.close()

        os.chmod(jobFile, stat.S_IRWXU)

    def combine(self):
        if self._status is not None:
            if self._status.is_stopped():
                self._status.cleanup()
            else:
                self._status.update()

    def _run_monoprocessor(self):
        for index in range(self.numberOfSteps):
            idx, result = self.run_step(index)
            self.combine(idx, result)

    def _run_threadpool(self):
        def helper(self, index):
            idx, result = self.run_step(index)
            self.combine(idx, result)

        pool = PoolExecutor(max_workers=self.configuration["running_mode"]["slots"])

        futures = [
            pool.submit(helper, self, index) for index in range(self.numberOfSteps)
        ]
        results = [future.result() for future in futures]

    def process_tasks_queue(self, tasks, outputs):
        while True:
            try:
                index = tasks.get_nowait()
            except queue.Empty:
                if tasks.empty():
                    self.configuration["trajectory"]["instance"].close()
                    break
            else:
                output = self.run_step(index)
                outputs.put(output)

        return True

    def _run_multiprocessor(self):
        oldrecursionlimit = sys.getrecursionlimit()
        sys.setrecursionlimit(100000)

        ctx = multiprocessing.get_context("spawn")

        manager = ctx.Manager()
        inputQueue = manager.Queue()
        outputQueue = manager.Queue()

        processes = []

        for i in range(self.numberOfSteps):
            inputQueue.put(i)

        for i in range(self.configuration["running_mode"]["slots"]):
            p = multiprocessing.Process(
                target=self.process_tasks_queue, args=(inputQueue, outputQueue)
            )
            processes.append(p)
            p.daemon = False
            p.start()

        for p in processes:
            p.join()

        while True:
            try:
                index, result = outputQueue.get_nowait()
            except queue.Empty:
                break
            else:
                self.combine(index, result)

        sys.setrecursionlimit(oldrecursionlimit)

    def _run_remote(self):
        IJob.set_pyro_server()

        import MDANSE.DistributedComputing.MasterSlave as MasterSlave

        tasks = MasterSlave.initializeMasterProcess(
            self._name, slave_module="MDANSE.DistributedComputing.Slave"
        )

        tasks.setGlobalState(job=self)

        if self._status is not None:
            self._status.start(self.numberOfSteps, rate=0.1)

        for index in range(self.numberOfSteps):
            tasks.requestTask("run_step", MasterSlave.GlobalStateValue(1, "job"), index)

        for index in range(self.numberOfSteps):
            _, _, (idx, x) = tasks.retrieveResult("run_step")
            self.combine(idx, x)

        if self._status is not None:
            if self._status.is_stopped():
                self._status.cleanup()
                return
            else:
                self._status.update()

    _runner = {
        "monoprocessor": _run_monoprocessor,
        "threadpool": _run_threadpool,
        "multiprocessor": _run_multiprocessor,
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
                self._status.start(self.numberOfSteps, rate=0.1)
                self._status.state["info"] = str(self)

            if getattr(self, "numberOfSteps", 0) <= 0:
                raise JobError(self, "Invalid number of steps for job %s" % self._name)

            if "running_mode" in self.configuration:
                mode = self.configuration["running_mode"]["mode"]
            else:
                mode = "monoprocessor"

            IJob._runner[mode](self)

            self.finalize()

            if self._status is not None:
                self._status.finish()
        except:
            tb = traceback.format_exc()
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
    # Here a basic example of a job that will use a HDF trajectory, a frame selection and an output file in HDF5 and ASCII file formats
    settings = collections.OrderedDict()
    settings['trajectory']=('hdf_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['output_files']=('output_files', {"formats":["HDFFormat","netcdf","ASCIIFormat"]})
            
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
        self._outputData.write(self.configuration['output_files']['root'], self.configuration['output_files']['formats'], self._info)
        
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
