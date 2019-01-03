from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class Backbone(ISelector):

    section = "biopolymers"

    def select(self, *args):
        '''
        Returns the backbone atoms.
        
        Only for Protein, PeptideChain and NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.backbone().atomList()])
            except AttributeError:
                pass
            
        return sel

REGISTRY["backbone"] = Backbone
