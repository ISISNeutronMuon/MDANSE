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

from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable

from MDANSE.Core.SubclassFactory import SubclassFactory


class QVectorsError(Error):
    pass


class IQVectors(Configurable, metaclass=SubclassFactory):
    is_lattice = False

    def __init__(self, chemical_system, status=None):
        Configurable.__init__(self)

        self._chemical_system = chemical_system

        self._status = status

    @abc.abstractmethod
    def _generate(self):
        pass

    def generate(self):
        self._generate()

        if self._status is not None:
            self._status.finish()

    def setStatus(self, status):
        self._status = status
