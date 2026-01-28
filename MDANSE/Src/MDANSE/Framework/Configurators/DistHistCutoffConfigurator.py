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

from math import floor

from .DistCutoffConfigurator import get_largest_cutoff
from .IConfigurator import PredictionSettings
from .RangeConfigurator import RangeConfigurator



class DistHistCutoffConfigurator(RangeConfigurator):
    """Range of interatomic distances for a histogram.

    It does not allow distances large enough to include
    the periodic image of any atom in the system.
    """

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._max_value = kwargs.get("max_value", True)
        self.prediction = PredictionSettings(
            key="value",
            label="Interatomic distance",
        )

    def configure(self, value):
        """Configure the distance histogram cutoff configurator.

        Parameters
        ----------
        value : tuple
            A tuple of the range parameters.
        """
        if not self.update_needed(value):
            return

        if self._max_value and value[1] > floor(self.get_max_cutoff() * 100) / 100:
            self.error_status = (
                "The cutoff distance goes into the simulation box periodic images."
            )
            return

        super().configure(value)

    def get_max_cutoff(self):
        traj_config = self.configurable[self.dependencies["trajectory"]][
            "instance"]
        return get_largest_cutoff(traj_config)
