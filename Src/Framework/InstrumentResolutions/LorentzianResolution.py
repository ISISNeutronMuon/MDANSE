import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution
                 
class LorentzianInstrumentResolution(IInstrumentResolution):
    """
    Defines an instrument resolution with a lorentzian response
    """
    
    settings = collections.OrderedDict()
    settings['mu'] = ('float', {"default":0.0})
    settings['sigma'] = ('float', {"default":1.0})

    def set_kernel(self, omegas, dt):

        mu = self._configuration["mu"]["value"]
        sigma = self._configuration["sigma"]["value"]
                                          
        self._omegaWindow = (2.0*sigma)/((omegas-mu)**2 + sigma**2)
        self._timeWindow = numpy.fft.fftshift(numpy.fft.ifft(numpy.fft.ifftshift(self._omegaWindow))/dt)
    
REGISTRY['lorentzian'] = LorentzianInstrumentResolution
            
