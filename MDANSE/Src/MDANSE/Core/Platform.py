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
import os
import platform
from pathlib import Path


class PlatformError(Exception):
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

    def pid(self):
        """
        Return the pid of the process that currently runs MDANSE.

        :return: the pid of the process running MDANSE
        :rtype: int
        """

        return os.getpid()

    def base_directory(self):
        """
        Returns the path for MDANSE base directory.

        @return: the path for MDANSE base directory.
        @rtype: str
        """

        return Path(__file__).parents[2]


class PlatformPosix(Platform):
    """
    Base class for POSIX derived OS.
    """

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
