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

import os, string, sys

# Use the gzip module for Python version 1.5.2 or higher
gzip = None
try:
    _version = [int(c) for c in string.split(string.split(sys.version)[0], ".")]

    if _version >= [1, 5, 2]:
        try:
            import gzip
        except ImportError:
            gzip = None
except:
    pass


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
            import urllib.request, urllib.parse, urllib.error

            self.file = urllib.request.urlopen(filename)
        else:
            filename = os.path.expanduser(filename)
            if mode in ["r", "rt"]:
                if not os.path.exists(filename):
                    raise IOError((2, "No such file or directory: " + filename))
                if filename[-2:] == ".Z":
                    self.file = os.popen("uncompress -c " + filename, mode)
                elif filename[-3:] == ".gz":
                    if gzip is None:
                        self.file = os.popen("gunzip -c " + filename, mode)
                    else:
                        self.file = gzip.GzipFile(filename, "rb")
                elif filename[-4:] == ".bz2":
                    self.file = os.popen("bzip2 -dc " + filename, mode)
                else:
                    try:
                        self.file = open(filename, mode)
                    except IOError as details:
                        if type(details) == type(()):
                            details = details + (filename,)
                        raise IOError(details)
            elif mode == "w":
                if filename[-2:] == ".Z":
                    self.file = os.popen("compress > " + filename, mode)
                elif filename[-3:] == ".gz":
                    if gzip is None:
                        self.file = os.popen("gzip > " + filename, mode)
                    else:
                        self.file = gzip.GzipFile(filename, "wb")
                elif filename[-4:] == ".bz2":
                    self.file = os.popen("bzip2 > " + filename, mode)
                else:
                    try:
                        self.file = open(filename, mode)
                    except IOError as details:
                        if type(details) == type(()):
                            details = details + (filename,)
                        raise IOError(details)
            elif mode == "a":
                if filename[-2:] == ".Z":
                    raise IOError((0, "Can't append to .Z files"))
                elif filename[-3:] == ".gz":
                    if gzip is None:
                        self.file = os.popen("gzip >> " + filename, "w")
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
