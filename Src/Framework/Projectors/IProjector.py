from MDANSE.Core.Error import Error

class ProjectorError(Error):
    pass

class IProjector(object):
    
    _registry = 'projector'
        
    def __init__(self):
        
        self._axis = None
        
        self._projectionMatrix = None
                    
    def __call__(self, value):
        
        raise NotImplementedError
    
    def set_axis(self, axis):

        raise NotImplementedError
    
    @property
    def axis(self):
        
        return self._axis
        
