from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class MoleculeIndex(ISelector):

    section = "molecules"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(range(len(self._universe.objectList())))    

    def select(self, values):
        '''
        Returns the atoms that matches a given list of molecule indexes.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param indexes: the molecule indexes list.
        @type indexes: list
        '''
        
        sel = set()

        if '*' in values:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([int(v) for v in values])

            objList = self._universe.objectList()
        
            sel.update([at for v in vals for at in objList[v].atomList()])
        
        return sel

REGISTRY["molecule_index"] = MoleculeIndex
