from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class CarbonAlpha(ISelector):

    section = "proteins"

    def select(self, *args):
        '''
        Returns the c_alpha atoms.
        
        Only for Protein and PeptideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()
        
        for obj in self._universe.objectList():            
            try:            
                sel.update([at for at in obj.atomList() if at.name.strip().lower() == 'c_alpha'])
            except AttributeError:
                pass

        return sel

REGISTRY["carbon_alpha"] = CarbonAlpha
