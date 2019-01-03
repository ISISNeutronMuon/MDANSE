from MDANSE import REGISTRY
from MDANSE.Framework.Projectors.IProjector import IProjector

class NullProjector(IProjector):

    def set_axis(self, axis):
        pass
    
    def __call__(self, value):
        
        return value

REGISTRY['null'] = NullProjector
        
