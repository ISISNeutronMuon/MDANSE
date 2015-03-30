import abc
import glob
import os
import random
import stat
import string
import subprocess
import sys

from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Core.Configurable import Configurable
from MDANSE.Framework.Jobs.JobStatus import JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData

class JobError(Error):
    pass

def key_generator(size=4, chars=None, prefix=""):
    
    if chars is None:
        chars = string.ascii_lowercase + string.digits
    
    key = ''.join(random.choice(chars) for _ in range(size))
    if prefix:
        key = "%s_%s" % (prefix,key)
    
    return key
        
class IJob(Configurable):
    """
    This class handles a MDANSE job. In MDANSE any task modeled by a loop can be considered a MDANSE job. 
    """
            
    __metaclass__ = REGISTRY
    
    type = "job"
    
    section = "job"
        
    @staticmethod
    def set_name():
        """
        Sets a name for the job that is not already in use by another running job.
        """
        
        prefix = '%d' % PLATFORM.pid()
    
        # The list of the registered jobs.
        registeredJobs = [os.path.basename(f) for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
        
        while True:     
    
            # Followed by 4 random letters.
            name = key_generator(4, prefix=prefix)
            
            if not name in registeredJobs:
                break
                        
        return name
        
    def __init__(self, status=None):
        """
        The base class constructor.        
        """

        Configurable.__init__(self)
                
        self._outputData = OutputData()

        self._name = IJob.set_name()
        
        self._info = ""
                                        
        if status is not None:
            self._status = JobStatus(self)
        else:
            self._status = None
                                
    def build_documentation(self):
                
        doc = [self.__doc__]
        for conf in self.configurators.values():
            if conf.__doc__ is None:
                doc.append("%s : %s\n" % (conf.type,'undocumented'))
            else:
                doc.append("%s : %s\n" % (conf.type,conf.__doc__))
                
        doc = '\n'.join(doc)
           
        return doc
    
    @classmethod
    def build_parallelization_test(cls, testFile, parameters=None):
        """
        Produce a file like object for a given job.\n
        :Parameters:
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """
         
        # Try to open the output test file to see whether it is allowed.
        try:
            f = open(testFile, 'w')
        # Case where for whatever reason, the file could not be opened for writing. Return.        
        except IOError as e:
            raise JobError(["Error when saving python batch file.",e])
           
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)

        f.write('import os\n')
        f.write('import unittest\n')
        f.write('import numpy\n')
        f.write('from Scientific.IO.NetCDF import NetCDFFile\n')
        f.write('from Tests.UnitTest import UnitTest\n')
        f.write('from MDANSE import REGISTRY\n\n')
                
        f.write('class Test%sParallel(UnitTest):\n\n' % cls.type.upper())
        f.write('    def setUp(self):\n')
        f.write('        from MDANSE import LOGGER\n')
        f.write('        LOGGER.stop()\n\n')
                    
        f.write('    def test(self):\n')      

        # Writes the line that will initialize the |parameters| dictionary.
        f.write('        parameters = {}\n')
        
        for k, v in sorted(parameters.items()):
            f.write('        parameters[%r] = %r\n' % (k, v))
                
        f.write('\n        job = REGISTRY[%r](%r)\n\n' % ('job',cls.type))

        f.write('        parameters["running_mode"] = ("monoprocessor",1)\n')
        f.write('        self.assertNotRaises(job.run,parameters,False)\n\n')

        f.write('        f = NetCDFFile(job.configuration["output_files"]["files"][0],"r")\n')
        f.write('        resMono = {}\n')
        f.write('        for k,v in f.variables.items():\n')
        f.write('            resMono[k] = v.getValue()\n')
        f.write('        f.close()\n\n')

        f.write('        parameters["running_mode"] = ("multiprocessor",2)\n')
        f.write('        self.assertNotRaises(job.run,parameters,False)\n\n')

        f.write('        f = NetCDFFile(job.configuration["output_files"]["files"][0],"r")\n')
        f.write('        resMulti = {}\n')
        f.write('        for k,v in f.variables.items():\n')
        f.write('            resMulti[k] = v.getValue()\n')
        f.write('        f.close()\n\n')

        f.write('        for k in resMono.keys():\n')
        f.write('            self.assertTrue(numpy.allclose(resMono[k],resMulti[k]))\n\n')
            
        f.write('def suite():\n')
        f.write('    loader = unittest.TestLoader()\n')
        f.write('    s = unittest.TestSuite()\n')
        f.write('    s.addTest(loader.loadTestsFromTestCase(Test%sParallel))\n' % cls.type.upper())
        f.write('    return s\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    unittest.main(verbosity=2)\n')
        
        f.close()
        
        os.chmod(testFile,stat.S_IRWXU)

    @staticmethod
    def set_pyro_server():
    
        import Pyro.errors
        import Pyro.naming
    
        # Gets a Pyro proxy for the name server.
        locator = Pyro.naming.NameServerLocator()
    
        # Try to get an existing name server.        
        try:
            ns = locator.getNS()
            
        # Otherwise, start a new one.        
        except Pyro.errors.NamingError:
            
            subprocess.Popen([sys.executable, '-O', '-c', "import Pyro.naming; Pyro.naming.main([])"], stdout = subprocess.PIPE)
            ns = None
            while ns is None:
                try:
                    ns = locator.getNS()
                except Pyro.errors.NamingError:
                    pass
                            
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
    def run_step(self):
        pass
            
    @classmethod
    def save(cls, jobFile, parameters=None):
        """
        Save a job file for a given job.\n
        :Parameters:
            #. jobFile (str): The name of the output job file.\n
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """
                         
        # Try to open the output job file to see whether it is allowed.
        try:
            f = open(jobFile, 'w')
        
        # Case where for whatever reason, the file could not be opened for writing. Return.        
        except IOError as e:
            raise JobError(["Error when saving python batch file.",e])
           
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)
        
        # Writes the input file header.
        f.write('########################################################\n')
        f.write('# This is an automatically generated MDANSE run script #\n')
        f.write('#######################################################\n\n')
                                    
        # Write the import.
        f.write("from MDANSE import REGISTRY\n\n")
                        
        f.write('################################################################\n')
        f.write('# Job parameters                                               #\n')
        f.write('################################################################\n\n')

        # Writes the line that will initialize the |parameters| dictionary.
        f.write('parameters = {}\n')
        
        if parameters is None:
            parameters = cls.configurators.get_default_parameters()
        
        for k, v in sorted(parameters.items()):
            f.write('parameters[%r] = %r\n' % (k, v))

        f.write('\n')
        f.write('################################################################\n')
        f.write('# Setup and run the analysis                                   #\n')
        f.write('################################################################\n')
        f.write('\n')
    
        # Sets |analysis| variable to an instance analysis to save. 
        f.write('job = REGISTRY[%r][%r](status=False)\n' % ('job',cls.type))
        f.write('job.setup(parameters)\n')
        f.write('job.run()')
         
        f.close()
        
        os.chmod(jobFile,stat.S_IRWXU)
                
    @classmethod
    def build_test(cls, testFile, parameters=None):
        """
        Produce a file like object for a given job.\n
        :Parameters:
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """
                
        # Try to open the output test file to see whether it is allowed.
        try:
            f = open(testFile, 'w')
        # Case where for whatever reason, the file could not be opened for writing. Return.        
        except IOError as e:
            raise JobError(["Error when saving python batch file.",e])
           
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)

        f.write('import unittest\n')
        f.write('from Tests.UnitTest import UnitTest\n')
        f.write('from MDANSE import REGISTRY\n\n')
                
        f.write('class Test%s(UnitTest):\n\n' % cls.type.upper())
        f.write('    def setUp(self):\n')
        f.write('        from MDANSE import LOGGER\n')
        f.write('        LOGGER.stop()\n\n')
        
        f.write('    def test(self):\n')      

        # Writes the line that will initialize the |parameters| dictionary.
        f.write('        parameters = {}\n')
        
        if parameters is None:
            parameters = cls.configurators.get_default_parameters()
        
        for k, v in sorted(parameters.items()):
            f.write('        parameters[%r] = %r\n' % (k, v))
    
        # Sets |analysis| variable to an instance analysis to save. 
        f.write('        job = REGISTRY[%r](%r)\n' % ('job',cls.type))
        f.write('        self.assertNotRaises(job.run, parameters,False)\n\n')
        
        f.write('def suite():\n')
        f.write('    loader = unittest.TestLoader()\n')
        f.write('    s = unittest.TestSuite()\n')
        f.write('    s.addTest(loader.loadTestsFromTestCase(Test%s))\n' % cls.type.upper())
        f.write('    return s\n\n')
        f.write("if __name__ == '__main__':\n")
        f.write('    unittest.main(verbosity=2)\n')
        
        f.close()
        
        os.chmod(testFile,stat.S_IRWXU)
        
    def _run_monoprocessor(self):

        if self._status is not None:
            self._status.start(self.numberOfSteps,rate=0.1)

        for index in range(self.numberOfSteps):
            idx, x = self.run_step(index)                            
            self.combine(idx, x)
            
            if self._status is not None:
                if self._status.is_stopped():
                    self._status.cleanup()
                    return
                else:
                    self._status.update()
        
    def _run_multiprocessor(self):

        import MDANSE.DistributedComputing.MasterSlave as MasterSlave

        script = os.path.abspath(os.path.join(PLATFORM.package_directory(),'DistributedComputing','Slave.py'))
                
        master = MasterSlave.initializeMasterProcess(self._name, slave_script=script, use_name_server=False)

        master.setGlobalState(job=self)
        master.launchSlaveJobs(n=self.configuration['running_mode']['slots'],port=master.pyro_daemon.port)

        if self._status is not None:
            self._status.start(self.numberOfSteps,rate=0.1)

        for index in range(self.numberOfSteps):
            master.requestTask('run_step',MasterSlave.GlobalStateValue(1,'job'),index)
        
        for index in range(self.numberOfSteps):
            _, _, (idx, x) = master.retrieveResult('run_step')
            self.combine(idx, x)

            if self._status is not None:
                if self._status.is_stopped():
                    self._status.cleanup()
                    return
                else:
                    self._status.update()
            
        master.shutdown()
        
    def _run_remote(self):

        IJob.set_pyro_server()

        import MDANSE.DistributedComputing.MasterSlave as MasterSlave

        tasks = MasterSlave.initializeMasterProcess(self._name, slave_module='MDANSE.DistributedComputing.Slave')
             
        tasks.setGlobalState(job=self)

        if self._status is not None:
            self._status.start(self.numberOfSteps,rate=0.1)
                
        for  index in range(self.numberOfSteps):
            tasks.requestTask('run_step',MasterSlave.GlobalStateValue(1,'job'),index)

        for index in range(self.numberOfSteps):
            _, _, (idx, x) = tasks.retrieveResult("run_step")
            self.combine(idx, x)

        if self._status is not None:
            if self._status.is_stopped():
                self._status.cleanup()
                return
            else:
                self._status.update()
            
    _runner = {"monoprocessor" : _run_monoprocessor, "multiprocessor" : _run_multiprocessor, "remote" : _run_remote}

    def run(self, parameters=None):
        """
        Run the job.
        """
        
        if parameters is not None:
            self.setup(parameters)
        
        self.initialize()

        self._info = 'Information about %s job.\n' % self._name
        self._info += str(self)
                                                  
        LOGGER(self._info)
                  
        if getattr(self,'numberOfSteps', 0) <= 0:
            raise JobError("Invalid number of steps for job %s" % self)

        try:
            mode = self.configuration['running_mode']['mode']
        except:
            raise JobError("Invalid running mode")
        else:                        
            IJob._runner[mode](self)

        self.finalize()

        if self._status is not None:
            self._status.finish()

    @property
    def info(self):
            
        return self._info