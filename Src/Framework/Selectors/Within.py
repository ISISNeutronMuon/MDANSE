from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
               
class WithinSelection(ISelector):

    type = "within_selection"

    section = None

    def select(self, atoms, mini=0.0, maxi=1.0):

        sel = set()

        for at in atoms:
            sel.update([a for a in self._universe.selectShell(at.position(),mini,maxi).atomList()])
        
        return sel
    
REGISTRY["within_selection"] = WithinSelection
