from MMTK.Proteins import PeptideChain, Protein

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class ResidueName(ISelector):

    section = "proteins"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                for chain in obj:
                    self._choices.extend([r.fullName() for r in chain.residues()])
                        
    def select(self, names):
        '''
        Returns the atoms that matches a given list of peptide names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the residue names list.
        @type names: list
        '''
                        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:            
            vals = set([v.strip().lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    for r in obj.residues():
                        resName = r.fullName().strip().lower()
                        if resName in vals: 
                            sel.update([at for at in r.atomList()])
                except:
                    pass
                
        return sel
    
REGISTRY["residue_name"] = ResidueName
