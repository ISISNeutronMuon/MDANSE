# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Thiol.py
# @brief     Implements module/class/test Thiol
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
