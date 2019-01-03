from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class Methyl(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the methyl atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            carbons = [at for at in obj.atomList() if at.type.name.strip().lower() == 'carbon']
            for car in carbons:
                neighbours = car.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 3:
                    sel.update([car] + hydrogens)

        return sel

REGISTRY["methyl"] = Methyl
