from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class AtomIndex(ISelector):

    section = "atoms"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted([at.index for at in self._universe.atomList()]))

    def select(self, indexes):
        '''
        Returns the atoms that matches a given list of indexes.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param indexes: the atom indexes list.
        @type indexes: list
        '''
        
        sel = set()
        
        if '*' in indexes:

            sel.update([at for at in self._universe.atomList()])
        
        else:
            vals = set([int(v) for v in indexes])
            sel.update([at for at in self._universe.atomList() if at.index in vals])
            
        return sel        

REGISTRY["atom_index"] = AtomIndex
