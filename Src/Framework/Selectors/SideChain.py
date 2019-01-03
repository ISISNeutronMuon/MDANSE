from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
    
class SideChain(ISelector):

    section = "biopolymers"

    def select(self, *args):
        '''
        Returns the sidechains atoms.
    
        Only for Protein, PeptideChain and NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()
    
        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.sidechains().atomList()])
            except AttributeError:
                pass
        
        return sel
    
REGISTRY["sidechain"] = SideChain
