#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#71 avenue des Martyrs
#38000 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import abc
import glob
import os
import random
import stat
import string
import subprocess
import sys
import traceback

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Jobs.JobStatus import JobStatus
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData

class JobError(Error):
    '''
    This class handles any exception related to IJob-derived objects
    '''
    
    def __init__(self,job,message=None):
        '''
        Initializes the the object.
        
        :param job: the configurator in which the exception was raised
        :type job: IJob derived object
        '''

        trace = []                        

        tback = traceback.extract_stack()
        
        for tb in tback:
            trace.append(' -- '.join([str(t) for t in tb]))

        if message is None:
            message = sys.exc_info()[1]

        self._message = str(message)

        trace.append("\n%s" % self._message)

        trace = '\n'.join(trace)
                
        if job._status is not None:
            job._status._state["state"] = "aborted"
            job._status._state['traceback'] = trace
            job._status._state['info'] = job.info
            job._status.update(force=True)
            
    def __str__(self):
        
        return self._message

def key_generator(keySize, chars=None, prefix=""):
    
    if chars is None:
        chars = string.ascii_lowercase + string.digits
    
    key = ''.join(random.choice(chars) for _ in range(keySize))
    if prefix:
        key = "%s_%s" % (prefix,key)
    
    return key
        
class IJob(Configurable):
    """
    This class handles a MDANSE job. In MDANSE any task modeled by a loop can be considered as a MDANSE job. 
    """
            
    __metaclass__ = REGISTRY
    
    type = "job"
    
    section = "job"
    
    ancestor = []
        
    @staticmethod
    def define_unique_name():
        """
        Sets a name for the job that is not already in use by another running job.
        """
        
        prefix = '%d' % PLATFORM.pid()
    
        # The list of the registered jobs.
        registeredJobs = [os.path.basename(f) for f in glob.glob(os.path.join(PLATFORM.temporary_files_directory(),'*'))]
        
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
        
        self._status = None
                                            
    @classmethod
    def build_parallelization_test(cls, testFile, parameters=None):
        """
        Produce a file like object for a given job.\n
        :Parameters:
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """
         
        f = open(testFile, 'w')
           
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
        
        
        f = open(jobFile, 'w')
                   
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)
        
        # Writes the input file header.
        f.write('########################################################\n')
        f.write('# This is an automatically generated MDANSE run script #\n')
        f.write('########################################################\n\n')
                                    
        # Write the import.
        f.write("from MDANSE import REGISTRY\n\n")
                        
        f.write('################################################################\n')
        f.write('# Job parameters                                               #\n')
        f.write('################################################################\n\n')

        # Writes the line that will initialize the |parameters| dictionary.
        f.write('parameters = {}\n')
        
        if parameters is None:
            parameters = cls.get_default_parameters()
        
        for k, v in sorted(parameters.items()):
            f.write('parameters[%r] = %r\n' % (k, v))

        f.write('\n')
        f.write('################################################################\n')
        f.write('# Setup and run the analysis                                   #\n')
        f.write('################################################################\n')
        f.write('\n')
    
        f.write('job = REGISTRY[%r][%r]()\n' % ('job',cls.type))
        f.write('job.run(parameters,status=True)')
         
        f.close()
        
        os.chmod(jobFile,stat.S_IRWXU)
                
    @classmethod
    def build_test(cls, testFile, parameters=None):
        """
        Produce a file like object for a given job.\n
        :Parameters:
            #. parameters (dict): optional. If not None, the parameters with which the job file will be built.
        """
                
        f = open(testFile, 'w')
           
        # The first line contains the call to the python executable. This is necessary for the file to
        # be autostartable.
        f.write('#!%s\n\n' % sys.executable)

        f.write('import unittest\n')
        f.write('from Tests.UnitTests.UnitTest import UnitTest\n')
        f.write('from MDANSE import REGISTRY\n\n')
                
        f.write('class Test%s(UnitTest):\n\n' % cls.type.upper())
        
        f.write('    def test(self):\n')      

        # Writes the line that will initialize the |parameters| dictionary.
        f.write('        parameters = {}\n')
        
        if parameters is None:
            parameters = cls.get_default_parameters()
        
        for k, v in sorted(parameters.items()):
            f.write('        parameters[%r] = %r\n' % (k, v))
    
        # Sets |analysis| variable to an instance analysis to save. 
        f.write('        job = REGISTRY[%r][%r]()\n' % ('job',cls.type))
        f.write('        self.assertNotRaises(job.run, parameters, status=False)\n\n')
        
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

    def run(self,parameters,status=False):
        """
        Run the job.
        """
        
        try:
            
            self._name = IJob.define_unique_name()

            self._info = 'Information about %s job.\n' % self._name
                                                        
            if status:
                self._status = JobStatus(self)
            
            self.setup(parameters)
                                    
            self.initialize()

            self._info += str(self)
            
            if self._status is not None:
                self._status.start(self.numberOfSteps,rate=0.1)
                self._status.state['info'] = self._info
                                        
            if getattr(self,'numberOfSteps', 0) <= 0:
                raise JobError(self,"Invalid number of steps for job %s" % self._name)
    
            if self.configuration.has_key('running_mode'):
                mode = self.configuration['running_mode']['mode']
            else:
                mode = 'monoprocessor'
    
            IJob._runner[mode](self)
    
            self.finalize()
    
            if self._status is not None:
                self._status.finish()
        except:
            tb = traceback.format_exc()
            raise JobError(self,tb)

    @property
    def info(self):
            
        return self._info

    @classmethod
    def save_template(cls, shortname,classname):
                    
        if REGISTRY['job'].has_key(shortname):
            raise KeyError('A job with %r name is already stored in the registry' % shortname)
                        
        from MDANSE import PREFERENCES
        macrosDir =  PREFERENCES["macros_directory"].get_value()
        
        templateFile = os.path.join(macrosDir,"%s.py" % classname)
                
        try:            
            f = open(templateFile,'w')
        
            f.write(
'''import collections

from MDANSE.Framework.Jobs.IJob import IJob

class %s(IJob):
    """
    You should enter the description of your job here ...
    """
    
    type = %r
    
    # You should enter the label under which your job will be referenced from the gui.
    label = %r

    # You should enter the category under which your job will be references.
    category = ('My jobs',)
    
    ancestor = ["mmtk_trajectory"]

    # You should enter the configuration of your job here
    # Here a basic example of a job that will use a MMTK trajectory, a frame selection and an output file in NetCDF and ASCII file formats
    settings = collections.OrderedDict()
    settings['trajectory']=('mmtk_trajectory',{})
    settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
    settings['output_files']=('output_files', {"formats":["netcdf","ascii"]})
            
    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # Compulsory. You must enter the number of steps of your job.
        # Here for example the number of selected frames
        self.numberOfSteps = self.configuration['frames']['number']
                        
        # Create an output data for the selected frames.
        self._outputData.add("time", "line", self.configuration['frames']['time'], units='ps')


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
''' % (classname,shortname,classname))
        
        except IOError:
            return None
        else:
            f.close()        
            return templateFile