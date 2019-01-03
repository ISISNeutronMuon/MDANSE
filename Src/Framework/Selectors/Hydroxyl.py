# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Hydroxyl.py
# @brief     Implements module/class/test Hydroxyl
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
       
class Hydroxyl(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
         Returns the hydroxyl atoms.

         @param universe: the universe
         @type universe: MMTK.universe
         '''
        
        sel = set()

        for obj in self._universe.objectList():            
            oxygens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'oxygen']
            for oxy in oxygens:
                neighbours = oxy.bondedTo()
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                if len(hydrogens) == 1:
                    sel.update([oxy] + hydrogens)
  
        return sel
    
REGISTRY["hydroxyl"] = Hydroxyl
