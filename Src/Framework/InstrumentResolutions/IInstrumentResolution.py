import abc

from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable

class InstrumentResolutionError(Error):
    pass

class IInstrumentResolution(Configurable):
    
    _registry = "instrument_resolution"
    
    def __init__(self):
        
        Configurable.__init__(self)
                        
        self._omegaWindow = None

        self._timeWindow = None
        
    @abc.abstractmethod
    def set_kernel(self, omegas, dt):
        pass    
    
    @property
    def omegaWindow(self):
        
        if self._omegaWindow is None:
            raise InstrumentResolutionError("Undefined omega window")
        
        return self._omegaWindow

    @property
    def timeWindow(self):
        
        if self._timeWindow is None:
            raise InstrumentResolutionError("Undefined time window")
        
        return self._timeWindow
