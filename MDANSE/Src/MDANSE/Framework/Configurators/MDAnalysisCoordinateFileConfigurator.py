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

import MDAnalysis as mda

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

from .MultiInputFileConfigurator import MultiInputFileConfigurator


class MDAnalysisCoordinateFileConfigurator(MultiInputFileConfigurator):
    """Take one or more filenames of files containing atomic coordinates.

    Several trajectory files can be concatenated using this input,
    but only if they are all in the same format.
    """

    _default = ("", "AUTO")

    def __init__(self, name, wildcard="All files (*)", **kwargs):
        IConfigurator.__init__(self, name, **kwargs)
        self.wildcard = wildcard

    def configure(self, setting: tuple[str | list[str], str]):
        """
        Parameters
        ----------
        setting : tuple[Union[str, list], str]
            A tuple of a list of file names or a string of the list
            which can be converted to a list using literal_eval and a
            string of the coordinate file format.
        """
        values, format = setting
        super().configure(values)

        if format == "AUTO" or not self["filenames"]:
            self["format"] = None
        elif format in mda._READERS:
            self["format"] = format
        else:
            self.error_status = "MDAnalysis coordinate file format not recognised."
            return

        topology_configurator = self.configurable[self.dependencies["input_file"]]
        if not topology_configurator.valid:
            self.error_status = "Requires valid topology file."
            return

        try:
            if len(self["filenames"]) <= 1 or self["format"] is None:
                mda.Universe(
                    topology_configurator["filename"],
                    *self["filenames"],
                    format=self["format"],
                    topology_format=topology_configurator["format"],
                ).trajectory
            else:
                coord_files = [(i, self["format"]) for i in self["filenames"]]
                mda.Universe(
                    topology_configurator["filename"],
                    coord_files,
                    topology_format=topology_configurator["format"],
                ).trajectory

        except Exception as e:
            self.error_status = f"Unable to create MDAnalysis universe: {e}"
            return
