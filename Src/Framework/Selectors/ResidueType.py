# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ResidueType.py
# @brief     Implements module/class/test ResidueType
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import PeptideChain, Protein
from MDANSE.Framework.Selectors.ISelector import ISelector
        
class ResidueType(ISelector):

    section = "proteins"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)
                                
        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, (PeptideChain, Protein)):
                self._choices.extend([r.code.strip() for r in ce.residues])
                

    def select(self, types):
        '''
        Returns the atoms that matches a given list of peptide types.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the residue types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)):
                    sel.update([at for at in ce.atom_list()])
        
        else:                
            vals = set([v.strip() for v in types])

            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)):
                    for r in ce.residues:
                        resType = r.code.strip()
                        if resType in vals:
                            sel.update([at for at in r.atom_list()])
                
        return sel
    
REGISTRY["residue_type"] = ResidueType
