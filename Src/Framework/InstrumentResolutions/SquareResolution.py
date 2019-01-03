# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InstrumentResolutions/SquareResolution.py
# @brief     Implements module/class/test SquareResolution
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

class SquareInstrumentResolution(IInstrumentResolution):
    """Defines an instrument resolution with a square response
    """
    
    settings = collections.OrderedDict()
    settings['mu'] = ('float', {"default":0.0})
    settings['sigma'] = ('float', {"default":1.0})

    def set_kernel(self, omegas, dt):
                                
        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                                
        self._omegaWindow = 2.0*numpy.pi*numpy.where((numpy.abs(omegas-mu)-sigma) > 0,0.0,1.0/(2.0*sigma))
                        
        self._timeWindow = numpy.fft.fftshift(numpy.fft.ifft(numpy.fft.ifftshift(self._omegaWindow))/dt)

REGISTRY['square'] = SquareInstrumentResolution
    
