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

from MDANSE.NeutronInstruments.Resolution.Resolution import Resolution


class IdealResolution(Resolution):
    def resolution_window(self, energy_axis: np.ndarray, Ef: float, Ei: float):
        window_axis = np.linspace(0, energy_axis.max(), len(energy_axis))
        window_value = np.zeros_like(window_axis)
        window_value[0] = 1.0
        return window_value, window_axis
