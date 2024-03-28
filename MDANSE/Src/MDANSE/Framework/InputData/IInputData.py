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

from MDANSE.Core.Error import Error

from MDANSE.Core.SubclassFactory import SubclassFactory


class InputDataError(Error):
    """
    This class handles exception related to ``IInputData`` interface.
    """


class IInputData(metaclass=SubclassFactory):
    """
    This is the base class for handling MDANSE input data.
    """

    def __init__(self, name, *args):
        """
        Builds an ``IInputData`` object.
        """

        self._name = name

        self._data = None

    @property
    def name(self):
        """
        Returns the name associated with the input data.

        :return: the name associated with the input data.
        :rtype: str
        """

        return self._name

    @property
    def shortname(self):
        return self._name

    @property
    def data(self):
        """
        Return the input data.

        :return: the input data.
        :rtype: depends on the concrete ``IInputData`` subclass
        """

        return self._data

    def info(self):
        """
        Returns information as a string about the input data.

        :return:
        :rtype: str
        """

        return "No information available"
