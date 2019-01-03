from MMTK.Proteins import PeptideChain, Protein

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
        
class ResidueType(ISelector):

    section = "proteins"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                self._choices.extend([r.symbol.strip().lower() for r in obj.residues()])
                

    def select(self, types):
        '''
        Returns the atoms that matches a given list of peptide types.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the residue types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:                
            vals = set([v.strip().lower() for v in types])

            for obj in self._universe.objectList():
                try:
                    for r in obj.residues():
                        resType = r.symbol.strip().lower()
                        if resType in vals:
                            sel.update([at for at in r.atomList()])
                except AttributeError:
                    pass
                
        return sel
    
REGISTRY["residue_type"] = ResidueType
