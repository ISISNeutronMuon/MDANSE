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

from MDANSE.Framework.Configurators.FloatConfigurator import FloatConfigurator


class MDAnalysisTimeStepConfigurator(FloatConfigurator):
    """Input for the trajectory time step in the MDAnalysis converter.

    MDAnalysis will attempt to determine the correct value of the time step
    based on the input files. That value is not guaranteed to be correct.
    """

    _default = 0.0

    def configure(self, value):
        # if the value is not valid then we use the MDAnalysis
        # default values which maybe the time step in the input
        # files or 1 ps
        if not self.update_needed(value):
            return

        try:
            value = float(value)
        except (TypeError, ValueError):
            pass

        if value in {None, "", 0.0}:
            file_configurator = self.configurable[self.dependencies["topology_file"]]
            files_configurator = self.configurable[
                self.dependencies["coordinate_files"]
            ]
            if file_configurator.valid and files_configurator.valid:
                try:
                    coord_format = files_configurator["format"]
                    coord_files = files_configurator["filenames"]
                    if len(coord_files) <= 1 or coord_format is None:
                        value = mda.Universe(
                            file_configurator["filename"],
                            *coord_files,
                            format=coord_format,
                            topology_format=file_configurator["format"],
                        ).trajectory.ts.dt
                    else:
                        coord_files = [(i, coord_format) for i in coord_files]
                        value = mda.Universe(
                            file_configurator["filename"],
                            coord_files,
                            topology_format=file_configurator["format"],
                        ).trajectory.ts.dt
                except Exception as e:
                    self.error_status = (
                        f"Unable to determine a time step from MDAnalysis: {e}"
                    )
                    return
            else:
                self.error_status = "Unable to determine a time step from MDAnalysis"
                return

        super().configure(value)
