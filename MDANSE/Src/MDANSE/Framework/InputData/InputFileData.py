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

import abc
import os

from MDANSE.Framework.InputData.IInputData import IInputData


class InputFileData(IInputData):
    def __init__(self, filename, load=True):
        IInputData.__init__(self, filename)

        self._basename = os.path.basename(filename)
        self._dirname = os.path.dirname(filename)

        if load:
            self.load()

    @property
    def filename(self):
        """
        Returns the filename associated with the input data.

        :return: the filename associated with the input data.
        :rtype: str
        """

        return self._name

    @property
    def shortname(self):
        """
        Returns the shortname of the file associated with the input data.

        :return: the shortname of the file associated with the input data.
        :rtype: str
        """

        return self._basename

    @property
    def basename(self):
        """
        Returns the basename of the file associated with the input data.

        :return: the basename of the file associated with the input data.
        :rtype: str
        """

        return self._basename

    @property
    def dirname(self):
        return self._dirname

    @abc.abstractmethod
    def load(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass
