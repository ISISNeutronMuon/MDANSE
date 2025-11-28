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

import numpy as np

from MDANSE.Framework.Jobs.CartesianCorrelationFunction import (
    CartesianCorrelationFunction,
)


class PositionCorrelationFunction(CartesianCorrelationFunction):
    """Calculates the position correlation function.

    Like the velocity correlation function, but using positions instead of
    velocities.
    """

    enabled = True
    label = "Position Correlation Function"
    CF_NAME = "pcf"
    CF_UNITS = "nm2"
    MAIN_RESULTS = "pcf/isotropic/"

    def get_series(self, index):
        atom_index = self.trajectory.atom_indices[index]

        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )
        series = series - np.average(series, axis=0)
        series = self.configuration["projection"]["projector"](series)
        return series
