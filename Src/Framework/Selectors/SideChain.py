# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/SideChain.py
# @brief     Implements module/class/test SideChain
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import PeptideChain, Protein
from MDANSE.Framework.Selectors.ISelector import ISelector
    
class SideChain(ISelector):

    section = "proteins"

    def select(self, names):
        '''Returns the sidechains atoms.
    
        Only for Protein, PeptideChain and NucleotideChain objects.
        '''
        
        sel = set()

        if '*' in names:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain, Protein)):
                    sel.update(ce.sidechains)
        else:            
            vals = set(names)
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain, Protein)) and ce.name in vals:
                    sel.update(ce.sidechains)

        return sel

REGISTRY["sidechain"] = SideChain
