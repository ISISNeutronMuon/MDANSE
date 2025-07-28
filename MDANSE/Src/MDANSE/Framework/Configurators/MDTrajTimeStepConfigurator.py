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

import mdtraj as md

from MDANSE.Framework.Configurators.FloatConfigurator import FloatConfigurator


class MDTrajTimeStepConfigurator(FloatConfigurator):
    """Inputs the time step value for the MDTraj converter."""

    _default = 0.0

    def configure(self, value):
        # if the value is not valid then we use the MDTraj
        # default values which maybe the time step in the input
        # files or 1 ps
        if not self.update_needed(value):
            return

        try:
            value = float(value)
        except (TypeError, ValueError):
            pass

        if value in {None, "", 0.0}:
            coord_conf = self.configurable[self.dependencies["coordinate_files"]]
            top_conf = self.configurable[self.dependencies["topology_file"]]
            if coord_conf.valid and top_conf.valid:
                traj_files = coord_conf["filenames"]
                top_file = top_conf["filename"]
                try:
                    if top_file:
                        traj = md.load(traj_files, top=top_file)
                    else:
                        traj = md.load(traj_files)
                    if traj.n_frames == 1:
                        value = self._default
                    else:
                        value = float(traj.timestep)
                except Exception as e:
                    self.error_status = (
                        f"Unable to determine a time step from MDTraj: {e}"
                    )
                    return
            else:
                self.error_status = "Unable to determine a time step from MDTraj"
                return

        super().configure(value)
