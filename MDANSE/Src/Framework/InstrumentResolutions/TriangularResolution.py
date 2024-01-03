# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InstrumentResolutions/TriangularResolution.py
# @brief     Implements module/class/test TriangularResolution
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np


from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


class TriangularResolution(IInstrumentResolution):
    """Defines an instrument resolution with a triangular response"""

    settings = collections.OrderedDict()
    settings["mu"] = ("float", {"default": 0.0})
    settings["sigma"] = ("float", {"default": 1.0})

    def set_kernel(self, omegas, dt):
        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]

        val = np.abs(omegas - mu) - sigma

        self._omegaWindow = 2.0 * np.pi * np.where(val >= 0, 0.0, -val / sigma**2)

        self._timeWindow = np.fft.fftshift(
            np.fft.ifft(np.fft.ifftshift(self._omegaWindow)) / dt
        )
