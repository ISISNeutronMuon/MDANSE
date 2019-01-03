from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
    
class Thiol(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the thiol atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():

            sulphurs = [at for at in obj.atomList() if at.type.name.strip().lower() in ['sulphur', 'sulfur']]
            for sul in sulphurs:
                neighbours = sul.bondedTo()
                if not neighbours:
                    neighbours = self._universe.selectShell(sul,r1=0.0,r2=0.11)
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen'] 
                if len(hydrogens)==1:
                    sel.update([sul] + hydrogens)
                
        return sel
    
REGISTRY["thiol"] = Thiol
