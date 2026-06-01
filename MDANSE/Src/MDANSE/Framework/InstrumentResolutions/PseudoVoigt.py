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
from MDANSE.Framework.Parameters import Float


class PseudoVoigt(IInstrumentResolution):
    """Defines an instrument resolution with a pseudo-voigt response"""

    eta = Float(minimum=0.0, maximum=1.0, default=0.5)
    mu_lorentzian = Float(default=0.0)
    sigma_lorentzian = Float(default=1.0)
    mu_gaussian = Float(default=0.0)
    sigma_gaussian = Float(default=1.0)

    def set_kernel(self, omegas, dt):
        muL = self.mu_lorentzian
        sigmaL = self.sigma_lorentzian
        muG = self.mu_gaussian
        sigmaG = self.sigma_gaussian

        gaussian = (np.sqrt(2.0 * np.pi) / sigmaG) * np.exp(
            -0.5 * ((omegas - muG) / sigmaG) ** 2
        )

        lorentzian = (2.0 * sigmaL) / ((omegas - muL) ** 2 + sigmaL**2)

        self._omegaWindow = self.eta * lorentzian + (1.0 - self.eta) * gaussian
        self._timeWindow = self.apply_fft(self._omegaWindow, dt)
