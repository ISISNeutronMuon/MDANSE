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


class ProjectorError(Error):
    pass


class IProjector(metaclass=SubclassFactory):
    def __init__(self):
        self._axis = None

        self._projectionMatrix = None

    def __call__(self, value):
        raise NotImplementedError

    def set_axis(self, axis):
        raise NotImplementedError

    @property
    def axis(self):
        return self._axis
