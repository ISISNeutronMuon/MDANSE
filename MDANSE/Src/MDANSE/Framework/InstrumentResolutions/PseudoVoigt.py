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


class PseudoVoigt(IInstrumentResolution):
    """Defines an instrument resolution with a pseudo-voigt response"""

    settings = collections.OrderedDict()
    settings["eta"] = ("FloatConfigurator", {"mini": 0.0, "maxi": 1.0, "default": 0.5})
    settings["mu_lorentzian"] = ("FloatConfigurator", {"default": 0.0})
    settings["sigma_lorentzian"] = ("FloatConfigurator", {"default": 1.0})
    settings["mu_gaussian"] = ("FloatConfigurator", {"default": 0.0})
    settings["sigma_gaussian"] = ("FloatConfigurator", {"default": 1.0})

    def set_kernel(self, omegas, dt):
        eta = self._configuration["eta"]["value"]
        muL = self._configuration["mu_lorentzian"]["value"]
        sigmaL = self._configuration["sigma_lorentzian"]["value"]
        muG = self._configuration["mu_gaussian"]["value"]
        sigmaG = self._configuration["sigma_gaussian"]["value"]

        gaussian = (np.sqrt(2.0 * np.pi) / sigmaG) * np.exp(
            -0.5 * ((omegas - muG) / sigmaG) ** 2
        )

        lorentzian = (2.0 * sigmaL) / ((omegas - muL) ** 2 + sigmaL**2)

        self._omegaWindow = eta * lorentzian + (1.0 - eta) * gaussian
        self._timeWindow = self.apply_fft(self._omegaWindow, dt)
