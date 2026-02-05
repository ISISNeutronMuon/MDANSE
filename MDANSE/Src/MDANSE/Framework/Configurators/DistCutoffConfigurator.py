#    This file is part of MDANSE.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

import numpy as np

from .FloatConfigurator import FloatConfigurator


def get_largest_cutoff(traj_config) -> float:
    """Get the largest cutoff value for the given trajectories
    unit cells.

    Returns
    -------
    traj_config
        The trajectory configuration object
    """
    try:
        trajectory_array = np.array(
            [
                traj_config.unit_cell(frame)._unit_cell
                for frame in range(len(traj_config))
            ]
        )
    except Exception:
        return np.linalg.norm(traj_config.min_span)

    if np.allclose(trajectory_array, 0.0):
        return np.linalg.norm(traj_config.min_span)

    # calculated the radius of the largest sphere that can
    # fit into the unit cell
    min_d = np.min(trajectory_array, axis=0)
    vec_a, vec_b, vec_c = min_d

    cross_bc = np.cross(vec_b, vec_c)
    cross_ca = np.cross(vec_c, vec_a)
    cross_ab = np.cross(vec_a, vec_b)

    if any(np.allclose(vec, 0.0) for vec in (cross_bc, cross_ca, cross_ab)):
        raise ValueError("Trajectory contains invalid unit cell.")

    h_1 = abs(np.dot(vec_a, cross_bc)) / np.linalg.norm(cross_bc)
    h_2 = abs(np.dot(vec_b, cross_ca)) / np.linalg.norm(cross_ca)
    h_3 = abs(np.dot(vec_c, cross_ab)) / np.linalg.norm(cross_ab)

    return 0.5 * min(h_1, h_2, h_3)


class DistCutoffConfigurator(FloatConfigurator):
    """.

    It does not allow distances large enough to include
    the periodic image of any atom in the system.
    """

    def configure(self, value):
        """Configure the distance histogram cutoff configurator.

        Parameters
        ----------
        value : tuple
            A tuple of the range parameters.
        """
        super().configure(value)

        if float(value) > round(self.get_max_cutoff(), 2):
            self.error_status = (
                "The cutoff distance goes into the simulation box periodic images."
            )
            return

    def get_max_cutoff(self):
        traj_config = self.configurable[self.dependencies["trajectory"]]["instance"]
        return get_largest_cutoff(traj_config)
