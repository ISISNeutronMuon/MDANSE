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

from contextlib import suppress
from typing import SupportsFloat

from MDANSE.Framework.Configurators.FloatConfigurator import FloatConfigurator
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

with suppress(ImportError):
    import MDAnalysis as mda


@IConfigurator.register("MDAnalysisTimeStepConfigurator")
class MDAnalysisTimeStepConfigurator(FloatConfigurator):
    """Input for the trajectory time step in the MDAnalysis converter.

    MDAnalysis will attempt to determine the correct value of the time step
    based on the input files. That value is not guaranteed to be correct.
    """

    _default = 0.0

    def configure(self, value: SupportsFloat | None) -> None:
        # if the value is not valid then we use the MDAnalysis
        # default values which maybe the time step in the input
        # files or 1 ps
        if not self.update_needed(value):
            return

        with suppress(TypeError, ValueError):
            value = float(value)

        if value in {None, "", 0.0}:
            files_configurator = self.configurable[
                self.dependencies["coordinate_files"]
            ]

            if not files_configurator.valid:
                self.error_status = "Unable to determine a time step from MDAnalysis."
                return

            value = files_configurator["instance"].trajectory.ts.dt

        super().configure(value)
