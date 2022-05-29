# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/AtomSymbol.py
# @brief     Implements module/class/test AtomSymbol
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

class AtomSymbol(ISelector):

    section = "atoms"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)
                
        self._choices.extend(sorted(set([at.symbol.strip() for at in self._chemicalSystem.atom_list()])))

    def select(self, symbols):
        '''Returns the atoms that matches a given list of atom types.
            
        @param types: the atom types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in symbols:

            sel.update([at for at in self._chemicalSystem.atom_list()])

        else:

            vals = set([v for v in symbols])
            sel.update([at for at in self._chemicalSystem.atom_list() if at.symbol.strip() in vals])
        
        return sel

REGISTRY["atom_symbol"] = AtomSymbol
