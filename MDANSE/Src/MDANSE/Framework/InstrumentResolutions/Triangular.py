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

import collections

import numpy as np


from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


class Triangular(IInstrumentResolution):
    """Defines an instrument resolution with a triangular response"""

    settings = collections.OrderedDict()
    settings["mu"] = ("FloatConfigurator", {"default": 0.0})
    settings["sigma"] = ("FloatConfigurator", {"default": 1.0})

    def set_kernel(self, omegas, dt):
        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]

        val = np.abs(omegas - mu) - sigma

        self._omegaWindow = 2.0 * np.pi * np.where(val >= 0, 0.0, -val / sigma**2)

        self._timeWindow = np.fft.fftshift(
            np.fft.ifft(np.fft.ifftshift(self._omegaWindow)) / dt
        )
