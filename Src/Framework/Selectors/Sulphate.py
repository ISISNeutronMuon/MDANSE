from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
        
class Sulphate(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the sulphate atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():

            sulphurs = [at for at in obj.atomList() if at.type.name.strip().lower() in ['sulphur', 'sulfur']]
            for sul in sulphurs:
                neighbours = sul.bondedTo()
                oxygens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'oxygen'] 
                if len(oxygens) == 4:
                    sel.update([sul] + oxygens)
                
        return sel
    
REGISTRY["sulphate"] = Sulphate
