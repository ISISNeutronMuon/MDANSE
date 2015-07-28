#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
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
import ctypes
import datetime
import getpass
import inspect
import os
import re
import subprocess
import tempfile
import types

from MDANSE.Core.Error import Error

class PlatformError(Error):
    '''
    This class handles error related to Platform derived classes.
    '''
    pass

class Platform(object):
    """
    This class implements platform-free standard operations.
    
    This is the base class for OS-specific concrete implementation.
    
    @note: this class is designed according to the singleton pattern.
    """
    
    __metaclass__ = abc.ABCMeta    

    __instance = None

    def __new__(cls, *args, **kwargs):
        '''
        Create a new instance of Platform class.
        
        :param cls: the class to instanciate.
        :type cls: class
        
        @note: designed using the Singleton pattern.
        '''
                
        # Case of the first instanciation.
        if cls.__instance is None:
            cls.__instance = super(Platform,cls).__new__(cls, *args, **kwargs)
                                
        return cls.__instance

    @abc.abstractmethod
    def application_directory(self):
        '''
        Returns the path for MDANSE application directory.
        
        This directory data used by MDANSE for running such a version of the MMTK database, 
        the preference file, the user definitions, the temporary job files directory ...
        
        :return: the path for MDANSE application directory.
        :rtype: str
        '''
        pass
    
    def doc_path(self):
        '''
        Returns the path for MDANSE documentation root directory.
        
        :return: the path for MDANSE documentation root directory
        :rtype: str
        '''

        return os.path.join(self.package_directory(), 'Doc')
    
    def api_path(self):
        '''
        Returns the path for MDANSE HTML API.
        
        :return: the path for MDANSE HTML documentation
        :rtype: str
        '''
        
        return os.path.join(self.package_directory(), 'Doc', 'api','html')

    def help_path(self):
        '''
        Returns the path for MDANSE HTML help.
        
        :return: the path for MDANSE HTML documentation
        :rtype: str
        '''
        
        return os.path.join(self.package_directory(), 'Doc', 'help','html')
    
    def local_mmtk_database_directory(self):
        '''
        Returns the path for MDANSE local MMTK database.
        
        :return: the path for MDANSE local MMTK database
        :rtype: str
        '''
        
        path = os.path.join(self.application_directory(), 'mmtk_database')
        
        # The first time the path for MMTK database directory is required, check whether some of the 
        # MMTK database subdirectories are present. If not, create them.
        if not os.path.exists(path):
            for mmtkDatabaseType in ['Atoms', 'Complexes', 'Crystals', 'Groups', 'Molecules', 'Proteins']:
                os.makedirs(os.path.join(path, mmtkDatabaseType))
                        
        return path
        
    def full_dotted_module(self,obj):
        '''
        Returns the fully dotted name of a module given the module object itself or a class stored in this module.
        
        :param obj: the module object or a class stored in stored in this module.
        :type obj: module or class
        
        :return: the fully dotted name of the module.
        :rtype: str
        '''
        
        if inspect.ismodule(obj):
            path = obj.__file__
        elif inspect.isclass(obj):
            path = inspect.getmodule(obj).__file__
        else:
            raise PlatformError('Invalid query object type.')
                    
        basepath = os.path.join(os.path.dirname(self.package_directory()),'')
                
        _,relativePath = path.split(basepath)
        
        relativePath = os.path.splitext(relativePath)[0]
                        
        return '.'.join(relativePath.split(os.path.sep))
        
    def change_directory(self, directory):
        '''
        Change the current directory to a new directory.
        
        :param directory: the new directory
        :type directory: str
        '''
        
        os.chdir(directory)
                    
    def is_directory_writable(self, path):
        '''
        Check whether a given directory is writable.
        
        :param path: the directory to be tested for writable status
        :type path: str
        
        :return: true if the directory is writable, false otherwise
        :rtype: bool
        '''

        # Gets an absolute version of the path to check
        path = self.get_path(path)
                
        # Case where the path to be checked does not exist
        if not os.path.exists(path):
        
            # Try to make the directory.
            try:
                os.makedirs(path)
        
            # An error occured, hence the path is not writable, return false
            except OSError:
                return False
            # No error occured, the user has permission to create the directory, so it will be writable
            else:
                return True
            
        # The directory to be checked already exists
        else:
            # Try to create a temporary file inside this directory             
            try:
                tempfile.TemporaryFile("w", path)
            # Failure, this directory is not writable
            except OSError:
                return False
            # Success, this directory is writable
            else: 
                return True    
                    
    def create_directory(self, path):
        '''
        Creates a directory.
        
        :param path: the path of the directory to create
        :type path: str
        '''
        
        path = self.get_path(path)
        
        if os.path.exists(path):
            return
        
        # Try to make the directory.
        try:
            os.makedirs(path)
        
        # An error occured.
        except OSError as e:
            raise PlatformError(e)
        
    def get_path(self, path):
        '''
        Return a normalized and absolute version of a given path
        
        :param path: the path of the file to be normalized and made absolute
        :type path: str
        
        :return: the normalized and absolute version of the input path
        :rtype: str
        '''
        
        path = str(path).encode('string-escape')      
                
        path = os.path.abspath(os.path.expanduser(path))
        
        return path
        
        
    def database_default_path(self):
        '''
        Returns the path for the default MDANSE elements database.
                        
        :return: the MDANSE default elements database path
        :rtype: string
        '''

        return os.path.join(self.package_directory(), 'Data', 'elements_database.csv')

    def database_user_path(self):
        '''
        Returns the path for user MDANSE elements database.
                
        :return: the MDANSE user elements database path.
        :rtype: string
        '''

        return os.path.join(self.application_directory(), 'elements_database.csv')

    @abc.abstractmethod
    def get_processes_info(self):
        '''
        Returns the current active processes.
 
        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict 
        '''        
        pass

    @abc.abstractmethod
    def kill_process(self, pid):
        '''
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        '''
        pass

    def pid(self):
        '''
        Return the pid of the process that currently runs MDANSE.
        
        :return: the pid of the process running MDANSE
        :rtype: int 
        '''
        
        return os.getpid()

    def example_data_directory(self):
        '''
        Returns the path for MDANSE example data (samples of trajectories, McStas files ...).
        
        :return: the path for MDANSE example files
        :rtype: str
        '''
        
        return os.path.join(os.path.dirname(self.package_directory()),'Data')

    def base_directory(self):
        '''
        Returns the path for MDANSE base directory.
        
        @return: the path for MDANSE base directory.
        @rtype: str        
        '''
        
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def package_directory(self):
        '''
        Returns the path for MDANSE package.
        
        @return: the path for MDANSE package.
        @rtype: str        
        '''
        
        return os.path.dirname(os.path.dirname(__file__))

    @abc.abstractmethod
    def preferences_file(self):
        '''
        Returns the path for MDANSE preferences file.

        :return: the path for the MDANSE preferences file
        :rtype: string
        
        :note: this path is OS specific.
        '''    
        pass

    def logfiles_directory(self):
        '''
        Returns the path of the directory where the MDANSE job logfiles are stored.
                
        :return: the path of the directory where the MDANSE job logfiles are stored..
        :rtype: str
        '''
       
        path = os.path.join(self.application_directory(), 'logfiles')
        
        self.create_directory(path)
                       
        return path

    def jobscripts_directory(self):
        '''
        Returns the path of the directory where the MDANSE job  script files are stored.
                
        :return: the path of the directory where the MDANSE job script files are stored.
        :rtype: str
        '''
       
        path = os.path.join(self.application_directory(), 'jobscripts')
        
        self.create_directory(path)
                       
        return path

    def temporary_files_directory(self):
        '''
        Returns the path of the directory where the temporary MDANSE job status files are stored.
                
        :return: the path of the directory where the temporary MDANSE job status files are stored
        :rtype: str
        '''
       
        path = os.path.join(self.application_directory(), 'temporary_files')
        
        self.create_directory(path)
                       
        return path
       
    def username(self):
        '''
        Returns the name of the user that run MDANSE.
        
        @return: the name of the user
        @rtype: str
        '''

        return getpass.getuser().lower()

    @abc.abstractmethod
    def home_directory(self):
        '''
        Returns the home directory of the user that runs MDANSE.
        
        @return: the home directory
        @rtype: str       
        '''
        pass

class PlatformPosix(Platform):
    '''
    Base class for POSIX derived OS.
    '''
    
    def home_directory(self):
        '''
        Returns the home directory of the user that runs MDANSE.
        
        @return: the home directory
        @rtype: str       
        '''
        
        return os.environ['HOME']

    def kill_process(self, pid):
        '''
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        '''
        
        import signal

        os.kill(pid, signal.SIGTERM)

    def application_directory(self):
        '''
        Returns the path for MDANSE application directory.
        
        This directory data used by MDANSE for running such a version of the MMTK database, 
        the preference file, the user definitions, the temporary job files directory ...
        
        :return: the path for MDANSE application directory.
        :rtype: str
        '''

        basedir = os.path.join(os.environ['HOME'], '.mdanse')
    
        # If the application directory does not exist, create it.
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        
        return basedir

    def preferences_file(self):
        '''
        Returns the path for MDANSE preferences file.

        :return: the path for the MDANSE preferences file
        :rtype: string
        
        :note: this path is OS specific.
        '''

        # The preferences files will be located in the application directory.        
        appdir = self.application_directory()
        
        return os.path.join(appdir, 'mdanse_preferences')


    def etime_to_ctime(self, etime):
        '''
        Converts the elapsed time (i.e. as output by ps unix command) to local time.
        
        :param etime: the elapsed time
        :type etime: str
        
        :return: the local time
        :rtype: str
        '''
                
        etime = [0, 0, 0] + [int(v) for v in re.split("-|:", etime)]
                
        days, hours, minutes, seconds = etime[-4:]
        
        etime = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                                              
        return (datetime.datetime.today() - etime).strftime("%d-%m-%Y %H:%M:%S")

    def get_processes_info(self):
        '''
        Returns the current active processes.
 
        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict 
        '''        
    
        # Get all the active processes using the Unix ps command
        procs = subprocess.Popen(['ps', '-o', 'pid,etime'], stdout=subprocess.PIPE)

        # The output of the ps command is splitted according to line feeds.
        procs = procs.communicate()[0].split('\n')[1:]
        
        # The list of (pid,executable).
        procs = [p.split() for p in procs if p]

        # A mapping between the active processes pid and their corresponding exectuable.
        procs = dict([(int(p[0].strip()), self.etime_to_ctime(p[1].strip())) for p in procs])
                        
        return procs

class PlatformMac(PlatformPosix):
    '''
    Concrete implementation of Platform interface for MacOS.
    '''

    name = "macos"

class PlatformLinux(PlatformPosix):
    '''
    Concrete implementation of Platform interface Linux.
    '''

    name = "linux"

class PlatformWin(Platform):
    '''
    Concrete implementation of Platform interface Windows.
    '''
    
    name = "windows"

    def application_directory(self):
        '''
        Returns the path for MDANSE application directory.
        
        This directory data used by MDANSE for running such a version of the MMTK database, 
        the preference file, the user definitions, the temporary job files directory ...
        
        :return: the path for MDANSE application directory.
        :rtype: str
        '''

        basedir = os.path.join(os.environ['APPDATA'], 'mdanse')
        
        # If the application directory does not exist, create it.
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        
        return basedir

    def get_process_creation_time(self, process):
        '''
        Return the creation time of a given process.
        
        :param process: the process to check for creation time
        :type process: int
        
        :return: the process creation time from time stamp
        :rtype: int
        '''
        
        creationtime = ctypes.c_ulonglong()
        exittime = ctypes.c_ulonglong()
        kerneltime = ctypes.c_ulonglong()
        usertime = ctypes.c_ulonglong()
        rc = ctypes.windll.kernel32.GetProcessTimes(process,
                                                    ctypes.byref(creationtime),
                                                    ctypes.byref(exittime),
                                                    ctypes.byref(kerneltime),
                                                    ctypes.byref(usertime))
        
        
        creationtime.value -= ctypes.c_longlong(116444736000000000L).value
        creationtime.value /= 10000000
        
        return creationtime.value    

    def get_processes_info(self):
        '''
        Returns the current active processes.
 
        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict 
  
        :note: Adapted from Eric Koome's implementation (http://code.activestate.com/recipes/305279-getting-process-information-on-windows/)
        '''
        
        DWORD = ctypes.c_ulong
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        
        parr = DWORD * 1024
        aProcesses = parr()
        cbNeeded = DWORD(0)
        hModule = DWORD()
                
        processes = {}

        # Call Enumprocesses to get hold of process id's
        ctypes.windll.psapi.EnumProcesses(ctypes.byref(aProcesses), ctypes.sizeof(aProcesses), ctypes.byref(cbNeeded))
    
        # Number of processes returned
        nReturned = cbNeeded.value / ctypes.sizeof(ctypes.c_ulong())
    
        pidProcess = [i for i in aProcesses][:nReturned]
    
        for pid in pidProcess:
        
            # Get handle to the process based on PID
            hProcess = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)

            if hProcess:
                                
                ctypes.windll.psapi.EnumProcessModules(hProcess, ctypes.byref(hModule), ctypes.sizeof(hModule), ctypes.byref(cbNeeded))
                        
                try:
                    creationTime = self.get_process_creation_time(hProcess)
                    creationTime = datetime.datetime.strftime(datetime.datetime.fromtimestamp(creationTime), "%d-%m-%Y %H:%M:%S")
                    processes[int(pid)] = creationTime
                except ValueError:
                    continue
                                        
                ctypes.windll.kernel32.CloseHandle(hProcess)

        return processes

    def home_directory(self):
        '''
        Returns the home directory of the user that runs MDANSE.
        
        @return: the home directory
        @rtype: str       
        '''
        
        return os.environ['USERPROFILE']

    
    def kill_process(self, pid):
        '''
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        '''
     
        PROCESS_TERMINATE = 1

        # Get the hadler of the process to be killed.    
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        
        # Terminate the process.
        ctypes.windll.kernel32.TerminateProcess(handle, -1)
        
        # Close the handle.
        ctypes.windll.kernel32.CloseHandle(handle)                
        
    def preferences_file(self):
        '''
        Returns the path for MDANSE preferences file.

        :return: the path for the MDANSE preferences file
        :rtype: string
        
        :note: this path is OS specific.
        '''    

        appdir = self.application_directory()
                
        return os.path.join(appdir, 'preferences.ini')
     
import platform
system = platform.system()

# Instantiate the proper platform class depending on the OS on which MDANSE runs
if system == 'Linux':
    PLATFORM=PlatformLinux()
elif system == "Darwin":
    PLATFORM=PlatformMac()
else:
    PLATFORM=PlatformWin()
del platform                
