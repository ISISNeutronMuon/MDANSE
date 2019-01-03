from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                    
class Amine(ISelector):
    '''
    Returns the amine atoms.
    '''

    section = "chemical groups"

    def select(self, *args):

        sel = set()
            
        for obj in self._universe.objectList():
                                        
            nitrogens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'nitrogen']
            
            for nit in nitrogens:
                neighbours = nit.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 2:
                    sel.update([nit] + [hyd for hyd in hydrogens])
                    
        return sel

REGISTRY["amine"] = Amine
