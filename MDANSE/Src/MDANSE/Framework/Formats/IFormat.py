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

from typing import TYPE_CHECKING

from MDANSE.Core.SubclassFactory import SubclassFactory

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.IJob import IJob


class IFormat(metaclass=SubclassFactory):
    """
    This is the base class for writing MDANSE output data. In MDANSE, the output of an analysis can be written in different file format.

    Currently, MDANSE supports HDF5 and Text output file formats. To introduce a new file output file format, just create a new concrete
    subclass of IFormat and overload the "write" class method as defined in IFormat base class which will actually write the output variables,
    and redefine the "type", "extension" and "extensions" class attributes.
    """

    @classmethod
    def write(cls, filename, data, header="", run_instance: IJob | None = None):
        """
        Write a set of output variables into filename using a given file format.

        :param filename: the path to the output file.
        :type filename: str
        :param data: the data to be written out.
        :type data: dict of Framework.OutputVariables.IOutputVariable
        :param header: the header to add to the output file.
        :type header: str
        :param run_instance: the instance of the job, to be queried for parameters
        :type run_instance: IJob
        """

        pass
