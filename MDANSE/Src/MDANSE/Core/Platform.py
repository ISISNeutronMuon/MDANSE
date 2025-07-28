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
import ctypes
import datetime
import getpass
import inspect
import os
import platform
import re
import subprocess
from pathlib import Path

from MDANSE.Core.Error import Error


class PlatformError(Error):
    """
    This class handles error related to Platform derived classes.
    """

    pass


class Platform(metaclass=abc.ABCMeta):
    """
    This is the base class for OS-free standard operations.
    """

    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Create a new instance of Platform class.

        :param cls: the class to instantiate.
        :type cls: class
        """

        # Case of the first instantiation.
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)

        return cls.__instance

    @abc.abstractmethod
    def application_directory(self) -> Path:
        """
        Returns the path for MDANSE application directory.

        The directory data used by MDANSE for storing preferences, databses, jobs temporary files ...

        :return: the path for MDANSE application directory.
        :rtype: Path
        """
        pass

    def doc_path(self) -> Path:
        """
        Returns the path for MDANSE documentation root directory.

        :return: the path for MDANSE documentation root directory
        :rtype: Path
        """

        return self.package_directory() / "Doc"

    def jobs_launch_delay(self) -> float:
        """
        Returns the delay (in seconds) for a job to launch.
        This is used to determine the delay before updating the GUI and suppressing a job status file

        :return: the delay (in seconds) for a job to launch
        :rtype: float
        """
        return 2.0

    def api_path(self) -> Path:
        """
        Returns the path for MDANSE HTML API.

        :return: the path for MDANSE HTML documentation
        :rtype: Path
        """

        return self.package_directory() / "Doc" / "api" / "html"

    def help_path(self) -> Path:
        """
        Returns the path for MDANSE HTML help.

        :return: the path for MDANSE HTML documentation
        :rtype: Path
        """

        return self.package_directory() / "Doc" / "help" / "html"

    def full_dotted_module(self, obj) -> str | None:
        """
        Returns the fully dotted name of a module given the module object itself or a class stored in this module.

        :param obj: the module object or a class stored in stored in this module.
        :type obj: module or class

        :return: the fully dotted name of the module.
        :rtype: str
        """

        if inspect.ismodule(obj):
            path = Path(obj.__file__)
        elif inspect.isclass(obj):
            path = Path(inspect.getmodule(obj).__file__)
        else:
            raise PlatformError("Invalid query object type.")

        basepath = self.package_directory().parent

        try:
            relativePath = path.relative_to(basepath)
        except ValueError:
            return None

        return ".".join(relativePath.with_suffix("").parts)

    def change_directory(self, directory: Path | str) -> None:
        """
        Change the current directory to a new directory.

        :param directory: the new directory
        :type directory: str
        """

        os.chdir(directory)

    @classmethod
    def is_file_writable(cls, filepath: Path | str) -> bool:
        """Check if the directories can be created and a file can be
        written into it.

        Parameters
        ----------
        filepath : str
            The filepath to test if the file can be written.

        Returns
        -------
        bool
            True if a file can be written.
        """
        filepath = cls.get_path(filepath)

        for direc in filepath.parents:
            if direc.exists():
                return os.access(direc, os.W_OK)

        return False

    def create_directory(self, path: Path | str) -> None:
        """
        Creates a directory.

        :param path: the path of the directory to create
        :type path: str
        """

        path = self.get_path(path)

        try:
            path.mkdir(parents=True, exist_ok=True)
        # An error occured.
        except OSError as err:
            raise PlatformError(
                f"Problem trying to create a directory at {path}"
            ) from err

    @classmethod
    def get_path(cls, path: Path | str) -> Path:
        """
        Return a normalized and absolute version of a given path

        :param path: the path of the file to be normalized and made absolute
        :type path: Path

        :return: the normalized and absolute version of the input path
        :rtype: Path
        """
        return Path(path).expanduser().absolute()

    def database_default_path(self):
        """
        Returns the path for the default MDANSE elements database.

        :return: the MDANSE default elements database path
        :rtype: string
        """

        return self.package_directory() / "Data" / "elements_database.csv"

    def database_user_path(self):
        """
        Returns the path for user MDANSE elements database.

        :return: the MDANSE user elements database path.
        :rtype: string
        """

        return self.application_directory() / "elements_database.csv"

    @abc.abstractmethod
    def get_processes_info(self):
        """
        Returns the current active processes.

        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict
        """
        pass

    @abc.abstractmethod
    def kill_process(self, pid):
        """
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        """
        pass

    def pid(self):
        """
        Return the pid of the process that currently runs MDANSE.

        :return: the pid of the process running MDANSE
        :rtype: int
        """

        return os.getpid()

    def example_data_directory(self):
        """
        Returns the path for MDANSE example data (samples of trajectories, McStas files ...).

        :return: the path for MDANSE example files
        :rtype: str
        """

        return self.package_directory().parent / "Data"

    def base_directory(self):
        """
        Returns the path for MDANSE base directory.

        @return: the path for MDANSE base directory.
        @rtype: str
        """

        return Path(__file__).parents[2]

    def package_directory(self) -> Path:
        """
        Returns the path for MDANSE package.

        @return: the path for MDANSE package.
        @rtype: Path
        """

        return Path(__file__).parent.parent

    def macros_directory(self) -> Path:
        """
        Returns the path of the directory where the MDANSE macros will be searched.

        :return: the path of the directory where the MDANSE macros will be searched.
        :rtype: Path
        """

        return self.application_directory() / "macros"

    def logfiles_directory(self) -> Path:
        """
        Returns the path of the directory where the MDANSE job logfiles are stored.

        :return: the path of the directory where the MDANSE job logfiles are stored.
        :rtype: Path
        """

        path = self.application_directory() / "logfiles"

        self.create_directory(path)

        return path

    def temporary_files_directory(self) -> Path:
        """
        Returns the path of the directory where the temporary MDANSE job status files are stored.

        :return: the path of the directory where the temporary MDANSE job status files are stored
        :rtype: Path
        """

        path = self.application_directory() / "temporary_files"

        self.create_directory(path)

        return path

    def username(self) -> str:
        """
        Returns the name of the user that run MDANSE.

        @return: the name of the user
        @rtype: str
        """

        return getpass.getuser().lower()

    @abc.abstractmethod
    def home_directory(self):
        """
        Returns the home directory of the user that runs MDANSE.

        @return: the home directory
        @rtype: str
        """
        pass


class PlatformPosix(Platform):
    """
    Base class for POSIX derived OS.
    """

    def home_directory(self):
        """
        Returns the home directory of the user that runs MDANSE.

        @return: the home directory
        @rtype: str
        """

        return os.environ["HOME"]

    def kill_process(self, pid):
        """
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        """

        import signal

        os.kill(pid, signal.SIGTERM)

    def application_directory(self):
        """
        Returns the path for MDANSE application directory.

        The directory data used by MDANSE for storing preferences, databses, jobs temporary files ...

        :return: the path for MDANSE application directory.
        :rtype: str
        """

        basedir = Path(os.environ["HOME"]) / ".mdanse"

        # If the application directory does not exist, create it.
        basedir.mkdir(exist_ok=True, parents=True)

        return basedir

    def etime_to_ctime(self, etime):
        """
        Converts the elapsed time (i.e. as output by ps unix command) to local time.

        :param etime: the elapsed time
        :type etime: str

        :return: the local time
        :rtype: str
        """

        etime = [0, 0, 0] + [int(v) for v in re.split("-|:", etime)]

        days, hours, minutes, seconds = etime[-4:]

        etime = datetime.timedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds
        )

        return (datetime.datetime.today() - etime).strftime("%d-%m-%Y %H:%M:%S")

    def get_processes_info(self):
        """
        Returns the current active processes.

        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict
        """

        # Get all the active processes using the Unix ps command
        process = subprocess.run(
            ["ps", "-eo", "pid,etime"],
            capture_output=True,
            check=True,
            text=True,
            shell=True,
        )
        procs = map(str.split, filter(None, process.stdout.splitlines()))
        procs = {int(pid): self.etime_to_ctime(etime.strip()) for pid, etime in procs}

        return procs


class PlatformMac(PlatformPosix):
    """
    Concrete implementation of :py:class:~MDANSE.Core.Platform.Platform interface for MacOS OS.
    """

    name = "macos"


class PlatformLinux(PlatformPosix):
    """
    Concrete implementation of :py:class:~MDANSE.Core.Platform.Platform interface for Linux OS.
    """

    name = "linux"


class PlatformWin(Platform):
    """
    Concrete implementation of :py:class:~MDANSE.Core.Platform.Platform interface for Windows OS.
    """

    name = "windows"

    def application_directory(self) -> Path:
        """
        Returns the path for MDANSE application directory.

        The directory data used by MDANSE for storing preferences, databses, jobs temporary files ...

        :return: the path for MDANSE application directory.
        :rtype: Path
        """

        basedir = Path(os.environ["APPDATA"]) / "mdanse"

        # If the application directory does not exist, create it.
        basedir.mkdir(parents=True, exist_ok=True)

        return basedir

    def get_process_creation_time(self, process) -> int:
        """
        Return the creation time of a given process.

        :param process: the process to check for creation time
        :type process: int

        :return: the process creation time from time stamp
        :rtype: int
        """

        creationtime = ctypes.c_ulonglong()
        exittime = ctypes.c_ulonglong()
        kerneltime = ctypes.c_ulonglong()
        usertime = ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetProcessTimes(
            process,
            ctypes.byref(creationtime),
            ctypes.byref(exittime),
            ctypes.byref(kerneltime),
            ctypes.byref(usertime),
        )

        creationtime.value -= ctypes.c_longlong(116444736000000000).value
        creationtime.value //= 10000000

        return creationtime.value

    def get_processes_info(self) -> dict:
        """
        Returns the current active processes.

        :return: a mapping between active processes pid and their corresponding process name.
        :rtype: dict

        :note: Adapted from Eric Koome's implementation (http://code.activestate.com/recipes/305279-getting-process-information-on-windows/)
        """

        DWORD = ctypes.c_ulong
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010

        parr = DWORD * 1024
        aProcesses = parr()
        cbNeeded = DWORD(0)
        hModule = DWORD()

        processes = {}

        # Call Enumprocesses to get hold of process id's
        ctypes.windll.psapi.EnumProcesses(
            ctypes.byref(aProcesses), ctypes.sizeof(aProcesses), ctypes.byref(cbNeeded)
        )

        # Number of processes returned
        nReturned = cbNeeded.value // ctypes.sizeof(ctypes.c_ulong())

        pidProcess = list(aProcesses)[:nReturned]

        for pid in pidProcess:
            # Get handle to the process based on PID
            hProcess = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
            )

            if hProcess:
                ctypes.windll.psapi.EnumProcessModules(
                    hProcess,
                    ctypes.byref(hModule),
                    ctypes.sizeof(hModule),
                    ctypes.byref(cbNeeded),
                )

                try:
                    creationTime = self.get_process_creation_time(hProcess)
                    creationTime = datetime.datetime.strftime(
                        datetime.datetime.fromtimestamp(creationTime),
                        "%d-%m-%Y %H:%M:%S",
                    )
                    processes[int(pid)] = creationTime
                except ValueError:
                    continue

                ctypes.windll.kernel32.CloseHandle(hProcess)

        return processes

    def home_directory(self) -> Path:
        """
        Returns the home directory of the user that runs MDANSE.

        @return: the home directory
        @rtype: Path
        """

        return Path(os.environ["USERPROFILE"])

    def kill_process(self, pid):
        """
        Kill a specified process.

        :param pid: the pid of the process to be killed.
        :type pid: int
        """

        PROCESS_TERMINATE = 1

        # Get the hadler of the process to be killed.
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)

        # Terminate the process.
        ctypes.windll.kernel32.TerminateProcess(handle, -1)

        # Close the handle.
        ctypes.windll.kernel32.CloseHandle(handle)


system = platform.system()
PLATFORM: Platform

# Instantiate the proper platform class depending on the OS on which MDANSE runs
if system == "Linux":
    PLATFORM = PlatformLinux()
elif system == "Darwin":
    PLATFORM = PlatformMac()
else:
    PLATFORM = PlatformWin()
del platform
