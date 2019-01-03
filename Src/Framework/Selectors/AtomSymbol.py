from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class AtomSymbol(ISelector):

    section = "atoms"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted(set([at.symbol.strip().lower() for at in self._universe.atomList()])))

    def select(self, types):
        '''
        Returns the atoms that matches a given list of atom types.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the atom types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([v.lower() for v in types])
            sel.update([at for at in self._universe.atomList() if at.symbol.strip().lower() in vals])
        
        return sel

REGISTRY["atom_symbol"] = AtomSymbol
