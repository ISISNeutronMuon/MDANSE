# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InstrumentResolutions/PseudoVoigtResolution.py
# @brief     Implements module/class/test PseudoVoigtResolution
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
        self._timeWindow = np.fft.fftshift(
            np.fft.ifft(np.fft.ifftshift(self._omegaWindow)) / dt
        )