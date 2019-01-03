import collections

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution

class IdealInstrumentResolution(IInstrumentResolution):
    """Defines an ideal instrument resolution with a Dirac response 
    """
        
    settings = collections.OrderedDict()

    def set_kernel(self, omegas, dt):
                
        nOmegas = len(omegas)
        self._omegaWindow = numpy.zeros(nOmegas, dtype=numpy.float64)
        self._omegaWindow[nOmegas/2] = 1.0

        self._timeWindow = numpy.ones(nOmegas, dtype=numpy.float64)
        
REGISTRY['ideal'] = IdealInstrumentResolution
