from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                                    
class Phosphate(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the phosphate atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()

        for obj in self._universe.objectList():

            phosphorus = [at for at in obj.atomList() if at.type.name.strip().lower() == 'phosphorus']
            for pho in phosphorus:
                neighbours = pho.bondedTo()
                oxygens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'oxygen'] 
                if len(oxygens) == 4:
                    sel.update([pho] + oxygens)
                
        return sel
    
REGISTRY["phosphate"] = Phosphate
