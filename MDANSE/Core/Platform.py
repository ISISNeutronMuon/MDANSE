"""
This modules implements actions or informations that are platform-specific.
"""

# Standards imports.
import abc
import ctypes
import datetime
import getpass
import os
import re
import subprocess

from MDANSE.Core.Error import Error

class PlatformError(Error):
    '''
    Handles error occuring in the module.
    '''
    pass

class Platform(object):
    """Virtual base class for platform-specific methods.
    
    @note: this class is designed according to the singleton pattern.
    """
    
    __metaclass__ = abc.ABCMeta

    __instance = None

    def __new__(cls, *args, **kwargs):
        '''
        Create a new instance of Platform class.
        
        @param cls: the class to instantiate.
        @type cls: class
        
        @note: designed using the Singleton pattern.
        '''

        # Case of the first instantiation.
        if cls.__instance is None:

            cls.__instance = super(Platform, cls).__new__(cls, *args, **kwargs)
                                
        # The selected instance is returned.
        return cls.__instance
    

    @abc.abstractmethod
    def application_directory(self):
        """Returns the path for MDANSE application directory.
        
        @return: the path for MDANSE application directory.
        @rtype: string

        @attention: this is an abstract method.
        """
        
        pass
    
    def documentation_path(self):
        return os.path.join(self.package_directory(), 'GUI', 'Help')
    
    def local_mmtk_database_directory(self):
        
        path = os.path.join(self.application_directory(), 'mmtk_database')
        
        if not os.path.exists(path):
            for mmtkDatabaseType in ['Atoms', 'Complexes', 'Crystals', 'Groups', 'Molecules', 'Proteins']:
                os.makedirs(os.path.join(path, mmtkDatabaseType))
                        
        return path
        
    def change_directory(self, directory):
        
        os.chdir(directory)
                    
    def is_directory_writable(self, path, testFile="junk.test.xxx"):

        path = self.get_path(path)
                
        if not os.path.exists(path):
        
            # Try to make the directory.
            try:
                os.makedirs(path)
        
            # An error occured.
            except OSError:
                return False
            
        testFile = os.path.join(path, testFile)
        
        try:
            f = open(testFile, "w")
        except IOError:
            return False
        else:
            f.close()
            os.unlink(testFile)
            return True
        
    def is_file_writable(self, path, delete=True):
        
        path = self.get_path(path)

        if not self.is_directory_writable(os.path.dirname(path)):
            return False
                    
        try:
            f = open(path, "w")
        except IOError:
            return False
        else:
            f.close()
            if delete:
                os.unlink(path)
            return True        
            
    def create_directory(self, path):
        
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
        
        path = str(path).encode('string-escape')      
                
        path = os.path.abspath(os.path.expanduser(path))
        
        return path
        
        
    def database_default_path(self):
        '''Returns the path for default mdanse database.
                
        @return: the mdanse database path.
        @rtype: string
        '''

        return os.path.join(self.package_directory(), 'Data', 'elements_database.csv')


    def database_user_path(self):
        '''Returns the path for user mdanse database.
                
        @return: the mdanse database path.
        @rtype: string
        '''

        return os.path.join(self.application_directory(), 'elements_database.csv')


    def database_path(self):
        '''Returns the path for mdanse database.
                
        @return: the mdanse database path.
        @rtype: string
        '''
                
        path = self.database_user_path()

        if os.path.exists(path):
            return path
        
        else:
            return self.database_default_path()


    @abc.abstractmethod
    def get_processes_info(self):
        '''Returns the active processes.
 
        @return: a mapping between active processes pid and their corresponding process name.
        @rtype: dict 

        @attention: this is an abstract method.
        '''
        
        pass

    
    @abc.abstractmethod
    def kill_process(self, pid):
        """Kill the specified process.

        @param process: the pid of the process to be killed.
        @type process: integer

        @attention: this is an abstract method.
        """

        pass


    def pid(self):
        
        return os.getpid()


    def package_directory(self):
        """Returns the path for mdanse package.
        
        @return: the path for mdanse package.
        @rtype: string
        """
        
        return os.path.dirname(os.path.dirname(__file__))


    @abc.abstractmethod
    def preferences_file(self):
        """Filename of our preferences file.

        @return: the filename of the mdanse preference file.
        @rtype: string
        
        @attention: this is an abstract method.
        """
    
        pass


    def standard_jobs_directory(self):
        '''Returns the mdanse jobs directory.
                
        @return: the mdanse jobs directory.
        @rtype: string
        '''
       
        basedir = self.package_directory()
       
        return os.path.join(basedir, 'Framework', 'Jobs')


    def temporary_files_directory(self):
        '''Returns the mdanse temporary files directory.
        
        It will contains the files containing the information about a running job.
        
        @return: the mdanse temporary files directory.
        @rtype: string
        '''
       
        path = os.path.join(self.application_directory(), 'temporary_files')
        
        self.create_directory(path)
                       
        return path
       
       
    def username(self):
        '''Returns the username for the running mdanse session..
        
        @return: the username.
        @rtype: string
        '''

        return getpass.getuser().lower()


class PlatformPosix(Platform):
    """Common Platform base class for Linux and Mac."""
    
    __metaclass__ = abc.ABCMeta


    def home_directory(self):
        """Returns the home directory.
        
        @return: the home directory
        @rtype: string
        """
        
        return os.environ['HOME']


    def kill_process(self, pid):
        """Kill the specified process.

        @param process: the pid of the process to be killed.
        @type process: integer
        """
        
        import signal

        os.kill(pid, signal.SIGTERM)


    def application_directory(self):
        """Returns the path for mdanse application directory.
        
        @return: the path for mdanse application directory.
        @rtype: string
        """

        basedir = os.path.join(os.environ['HOME'], '.mdanse')
    
        # If the application directory does not exist, create it.
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        
        return basedir


    def rename(self, src, dst):

        os.rename(src, dst)


    def preferences_file(self):
        """Filename of our preferences file.

        @return: the filename of the mdanse preference file.
        @rtype: string
        """

        # The preferences files will be located in the application directory.        
        appdir = self.application_directory()
        
        return os.path.join(appdir, 'mdanse_preferences')


    def etime_to_ctime(self, etime):
                
        etime = [0, 0, 0] + [int(v) for v in re.split("-|:", etime)]
                
        days, hours, minutes, seconds = etime[-4:]
        
        etime = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                                              
        return (datetime.datetime.today() - etime).strftime("%d-%m-%Y %H:%M:%S")


    def get_processes_info(self):
        '''Returns the active processes.
 
        @return: a mapping between active processes pid and their corresponding process name.
        @rtype: dict
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
    """
    Mac-specific platform object.
    """

    name = "macos"

class PlatformLinux(PlatformPosix):
    """
    Linux-specific platform object.
    """

    name = "linux"


class PlatformWin(Platform):
    """
    Win-specific platform object.
    """
    
    name = "windows"

    def application_directory(self):
        """Returns the path for mdanse application directory.
        
        @return: the path for mdanse application directory.
        @rtype: string
        """

        basedir = os.path.join(os.environ['APPDATA'], 'mdanse')
        
        # If the application directory does not exist, create it.
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        
        return basedir


    def get_process_creation_time(self, process):
        
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
        Returns the active processes.
 
        @return: a mapping between active processes pid and their corresponding process name.
        @rtype: dict
 
        @note: Based on information from http://support.microsoft.com/default.aspx?scid=KB;EN-US;Q175030&ID=KB;EN-US;Q175030
 
        @note: Adapted from Eric Koome original code
               email ekoome@yahoo.com
               license GPL
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
        """
        Returns the home directory.
        
        @return: the home directory
        @rtype: string
        """
        
        return os.environ['USERPROFILE']

    
    def kill_process(self, pid):
        """
        Kill the specified process.

        @param process: the pid of the process to be killed.
        @type process: integer
        """
     
        PROCESS_TERMINATE = 1

        # Get the hadler of the process to be killed.    
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        
        # Terminate the process.
        ctypes.windll.kernel32.TerminateProcess(handle, -1)
        
        # Close the handle.
        ctypes.windll.kernel32.CloseHandle(handle)                
        

    def rename(self, src, dst):

        if os.path.exists(dst):
            os.unlink(dst)
            
        os.rename(src, dst)
   
    
    def preferences_file(self):
        """Filename of our preferences file.
        
        @return: the filename of the mdanse preference file.
        @rtype: string
        """

        appdir = self.application_directory()
                
        return os.path.join(appdir, 'mdanse_preferences.ini')
     
import platform
system = platform.system()
# Instantiate the proper platform class depending on the OS.
if system == 'Linux':
    PLATFORM=PlatformLinux()
elif system == "Darwin":
    PLATFORM=PlatformMac()
else:
    PLATFORM=PlatformWin()
del platform                

    
