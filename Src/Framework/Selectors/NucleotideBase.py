from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class NucleotideBase(ISelector):

    section = "nucleic acids"

    def select(self, *args):
        '''
        Returns the bases atoms.
        
        Only for NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.bases().atomList()])
            except AttributeError:
                pass
            
        return sel
    
REGISTRY["nucleotide_base"] = NucleotideBase
