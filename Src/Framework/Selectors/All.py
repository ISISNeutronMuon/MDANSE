from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class All(ISelector):

    section = "miscellaneous"
                    
    def select(self, *args):
        return set(self._universe.atomList())

REGISTRY["all"] = All
                    
