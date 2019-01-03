from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                
class AtomFullName(ISelector):

    section = "atoms"

    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted(set([at.fullName().strip().lower() for at in self._universe.atomList()])))

    def select(self, names):
        '''
        Returns the atoms that matches a given list of atom names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the atom names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:

            sel.update([at for at in self._universe.atomList()])
            
        else:
            
            vals = set([v.lower() for v in names])
            sel.update([at for at in self._universe.atomList() if at.fullName().strip().lower() in vals])
        
        return sel

REGISTRY["atom_fullname"] = AtomFullName
