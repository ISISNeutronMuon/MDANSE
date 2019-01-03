# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InstrumentResolutions/GaussianResolution.py
# @brief     Implements module/class/test GaussianResolution
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution

class GaussianInstrumentResolution(IInstrumentResolution):
    """Defines an instrument resolution with a gaussian response
    """
    
    settings = collections.OrderedDict()
    settings['mu'] = ('float', {"default":0.0})
    settings['sigma'] = ('float', {"default":1.0})

    def set_kernel(self, omegas, dt):

        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                        
        self._omegaWindow = (numpy.sqrt(2.0*numpy.pi)/sigma)*numpy.exp(-0.5*((omegas-mu)/sigma)**2)
        self._timeWindow = numpy.fft.fftshift(numpy.fft.ifft(numpy.fft.ifftshift(self._omegaWindow))/dt)

REGISTRY['gaussian'] = GaussianInstrumentResolution
