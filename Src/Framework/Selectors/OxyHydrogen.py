# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/OxyHydrogen.py
# @brief     Implements module/class/test OxyHydrogen
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

class OxyHydrogen(ISelector):
        
    section = "hydrogens"

    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)

        for obj in self._universe.objectList():
                                        
            oxygens = [at for at in obj.atomList() if at.type.name.strip().lower() == 'oxygen']
            
            for oxy in oxygens:
                neighbours = oxy.bondedTo()
                hydrogens = [neigh.fullName().strip().lower() for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                self._choices.extend(sorted(hydrogens))
                
    def select(self, names):
    
        sel = set()

        if '*' in names:
            names = self._choices[1:]
            
        vals = set([v.lower() for v in names])
        sel.update([at for at in self._universe.atomList() if at.fullName().strip().lower() in vals])
        
        return sel
    
REGISTRY["oxy_hydrogen"] = OxyHydrogen
