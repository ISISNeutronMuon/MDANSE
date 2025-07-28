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

from pathlib import Path

from mdtraj.formats.registry import FormatRegistry

from .MultiInputFileConfigurator import MultiInputFileConfigurator


class MDTrajTrajectoryFileConfigurator(MultiInputFileConfigurator):
    """Passes one or more trajectory files to the MDTraj converter.

    Multiple files can be concatenated, but they have to be all in
    the same format.
    """

    def configure(self, value):
        super().configure(value)

        extensions = {"".join(Path(value).suffixes)[1:] for value in self["values"]}
        if len(extensions) != 1:
            self.error_status = "Files should be of a single format."
            return
        self.extension = next(iter(extensions))

        supported = list(i[1:] for i in FormatRegistry.loaders.keys())
        if self.extension not in supported:
            self.error_status = f"File '{self.extension}' not supported. Should be one of the following: {supported}"
            return
