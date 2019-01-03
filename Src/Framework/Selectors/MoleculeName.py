from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class MoleculeName(ISelector):

    section = "molecules"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
        
        self._choices.extend(sorted(set([obj.name for obj in self._universe.objectList()])))

    def select(self, names):
        '''
        Returns the atoms that matches a given list of molecule names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the molecule names list.
        @type names: list
        '''
        
        sel = set()
        
        if '*' in names:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([v.lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    if obj.name.strip().lower() in vals:
                        sel.update([at for at in obj.atomList()])
                except AttributeError:
                    pass
                
        return sel
    
REGISTRY["molecule_name"] = MoleculeName
