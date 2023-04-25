# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/AtomFullName.py
# @brief     Implements module/class/test AtomFullName
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                
class AtomFullName(ISelector):

    section = "atoms"

    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted(set([at.fullName().strip().lower() for at in self._universe.atomList()])))

    def select(self, names):
        '''
        Returns the atoms that matches a given list of atom names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the atom names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:

            sel.update([at for at in self._universe.atomList()])
            
        else:
            
            vals = set([v.lower() for v in names])
            sel.update([at for at in self._universe.atomList() if at.fullName().strip().lower() in vals])
        
        return sel

REGISTRY["atom_fullname"] = AtomFullName
