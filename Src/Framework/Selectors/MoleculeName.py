# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/MoleculeName.py
# @brief     Implements module/class/test MoleculeName
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

class MoleculeName(ISelector):

    section = "molecules"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)
        
        self._choices.extend(sorted(set([ce.name.strip() for ce in self._chemicalSystem.chemical_entities])))

    def select(self, names):
        '''
        Returns the atoms that matches a given list of molecule names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the molecule names list.
        @type names: list
        '''
        
        sel = set()
        
        if '*' in names:
            sel.update([at for at in self._chemicalSystem.atom_list()])

        else:
            vals = set(names)
            for ce in self._chemicalSystem.chemical_entities:
                if ce.name.strip() in vals:
                    sel.update([at for at in ce.atom_list()])
                
        return sel
    
REGISTRY["molecule_name"] = MoleculeName
