import abc

from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable

class QVectorsError(Error):
    pass

class IQVectors(Configurable):
        
    _registry = "q_vectors"

    is_lattice = False
            
    def __init__(self, universe, status=None):
        
        Configurable.__init__(self)
                                
        self._universe = universe
        
        self._status = status
            
    @abc.abstractmethod
    def _generate(self):
        pass
    
    def generate(self):
        
        self._generate()

        if self._status is not None:
            self._status.finish()
            
    def setStatus(self,status):
        
        self._status = status     
        
        
