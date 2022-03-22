# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Sulphate.py
# @brief     Implements module/class/test Sulphate
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
