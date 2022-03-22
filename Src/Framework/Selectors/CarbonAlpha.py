# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/CarbonAlpha.py
# @brief     Implements module/class/test CarbonAlpha
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

class CarbonAlpha(ISelector):

    section = "proteins"

    def select(self, *args):
        '''
        Returns the c_alpha atoms.
        
        Only for Protein and PeptideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''
        
        sel = set()
        
        for obj in self._universe.objectList():            
            try:            
                sel.update([at for at in obj.atomList() if at.name.strip().lower() == 'c_alpha'])
            except AttributeError:
                pass

        return sel

REGISTRY["carbon_alpha"] = CarbonAlpha
