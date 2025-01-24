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

"""
Text files with line iteration and transparent compression
"""

import os
import sys
from pathlib import Path
from contextlib import suppress

# Use the gzip module for Python version 1.5.2 or higher
with suppress(Exception):
    if sys.version_info >= (1, 5, 2):
        try:
            import gzip
        except ImportError:
            gzip = None
    else:
        gzip = None


class TextFile:
    """
    Text files with line iteration and transparent compression

    TextFile instances can be used like normal file objects
    (i.e. by calling read(), readline(), readlines(), and write()), but
    can also be used as sequences of lines in for-loops.

    TextFile objects also handle compression transparently. i.e. it is
    possible to read lines from a compressed text file as if it were not
    compressed.  Compression is deduced from the file name suffixes '.Z'
    (compress/uncompress), '.gz' (gzip/gunzip), and '.bz2' (bzip2).

    Finally, TextFile objects accept file names that start with '~' or
    '~user' to indicate a home directory, as well as URLs (for reading only).
    """

    def __init__(self, filename, mode="r"):
        """
        @param filename: file name or URL
        @type filename: C{str}
        @param mode: file access mode: 'r' (read), 'w' (write), or 'a' (append)
        @type mode: C{str}
        """

        self.file = None
        if filename.find(":/") > 1:  # URL
            if mode != "r":
                raise IOError("can't write to a URL")
            import urllib

            self.file = urllib.request.urlopen(filename)
        else:
            filename = Path(filename).expanduser()
            if mode in ["r", "rt"]:
                if not filename.exists():
                    raise IOError((2, f"No such file or directory: {filename}"))

                if filename.suffix == ".Z":
                    self.file = os.popen(f"uncompress -c {filename}", mode)

                elif filename.suffix == ".gz":
                    if gzip is None:
                        self.file = os.popen(f"gunzip -c {filename}", mode)
                    else:
                        self.file = gzip.GzipFile(filename, "rb")

                elif filename.suffix == ".bz2":
                    self.file = os.popen(f"bzip2 -dc {filename}", mode)

                else:
                    try:
                        self.file = open(filename, mode)
                    except IOError as details:
                        if isinstance(details, tuple):
                            details = details + (filename,)
                        raise IOError(details)

            elif mode == "w":
                if filename.suffix == ".Z":
                    self.file = os.popen(f"compress > {filename}", mode)

                elif filename.suffix == ".gz":
                    if gzip is None:
                        self.file = os.popen(f"gzip > {filename}", mode)
                    else:
                        self.file = gzip.GzipFile(filename, "wb")

                elif filename.suffix == ".bz2":
                    self.file = os.popen(f"bzip2 > {filename}", mode)

                else:
                    try:
                        self.file = open(filename, mode)
                    except IOError as details:
                        if isinstance(details, tuple):
                            details = details + (filename,)
                        raise IOError(details)

            elif mode == "a":
                if filename.suffix == ".Z":
                    raise IOError((0, "Can't append to .Z files"))
                elif filename.suffix == ".gz":
                    if gzip is None:
                        self.file = os.popen(f"gzip >> {filename}", "w")
                    else:
                        self.file = gzip.GzipFile(filename, "ab")
                else:
                    self.file = open(filename, mode)

            else:
                raise IOError((0, "Illegal mode: " + repr(mode)))

    def __del__(self):
        if self.file is not None:
            self.close()

    def __getitem__(self, item):
        line = self.file.readline()
        if not line:
            raise IndexError
        return line

    def read(self, size=-1):
        return self.file.read(size)

    def readline(self):
        return self.file.readline()

    def readlines(self):
        return self.file.readlines()

    def write(self, data):
        self.file.write(data)

    def writelines(self, list):
        for line in list:
            self.file.write(line)

    def close(self):
        self.file.close()

    def flush(self):
        self.file.flush()
