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

import collections

import numpy as np

from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


class Square(IInstrumentResolution):
    """Defines an instrument resolution with a square response"""

    settings = collections.OrderedDict()
    settings["mu"] = ("FloatConfigurator", {"default": 0.0})
    settings["sigma"] = ("FloatConfigurator", {"default": 1.0})

    def set_kernel(self, omegas, dt):
        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]

        self._omegaWindow = (
            2.0
            * np.pi
            * np.where((np.abs(omegas - mu) - sigma) > 0, 0.0, 1.0 / (2.0 * sigma))
        )

        self._timeWindow = self.apply_fft(self._omegaWindow, dt)
