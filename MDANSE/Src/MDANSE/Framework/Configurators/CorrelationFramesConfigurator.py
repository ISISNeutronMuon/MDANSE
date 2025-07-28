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

import math

from .FramesConfigurator import FramesConfigurator


class CorrelationFramesConfigurator(FramesConfigurator):
    """Parses the input of trajectory frames.

    Configures the time frame range to be used in the calculations
    together with a movable window used for correlations.
    """

    def configure(self, value: tuple[int, int, int, int]):
        """Set the number of correlation frames to use.

        Parameters
        ----------
        value : tuple[int, int, int, int]
            The frames setting plus the number of frames used for the
            correlations.

        """
        if not self.update_needed(value):
            return

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        n_steps = trajConfig["length"]

        # if all or None set to default
        if value in ["all", None]:
            value = [0, n_steps, 1, math.ceil(n_steps / 2)]

        first, last, step, c_frames = value
        super().configure((first, last, step))
        self._original_input = value

        if c_frames > self["n_frames"]:
            self.error_status = (
                "Number of frames used for the correlation "
                "greater than the total number of frames of "
                "the trajectory."
            )
            return

        if c_frames < 2:
            self.error_status = (
                "Number of frames used for the correlation should be greater then zero."
            )
            return

        self["n_frames"] = c_frames
        self["n_configs"] = self["number"] - c_frames + 1
        self["time"] = self["time"][:c_frames]
        self["duration"] = self["time"] - self["time"][0]
