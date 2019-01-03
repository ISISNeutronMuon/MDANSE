import abc

from MDANSE.Core.Error import Error

class SelectorError(Error):
    pass

class ISelector(object):
    
    _registry = "selector"
        
    def __init__(self,trajectory):
        
        self._universe = trajectory.universe
                
        self._choices = ["*"]

    @property
    def choices(self):
        return self._choices

    @abc.abstractmethod
    def select(self):
        pass
