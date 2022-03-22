# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/AtomType.py
# @brief     Implements module/class/test AtomType
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

class AtomType(ISelector):

    section = "atoms"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted(set([at.type.name.lower() for at in self._universe.atomList()])))

    def select(self, elements):
        '''
        Returns the atoms that matches a given list of elements.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param elements: the atom elements list.
        @type elements: list
        '''
                
        sel = set()
                
        if '*' in elements:

            sel.update([at for at in self._universe.atomList()])
        
        else:
            
            vals = [v.lower() for v in elements]
                
            if "sulfur" in vals:
                vals.append("sulphur")
            else:                    
                if "sulphur" in vals:
                    vals.append("sulfur")
                
            vals = set(vals)
            
            sel.update([at for at in self._universe.atomList() if at.type.name.strip().lower() in vals])

        return sel

REGISTRY["atom_type"] = AtomType
