# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ResidueName.py
# @brief     Implements module/class/test ResidueName
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

class ResidueName(ISelector):

    section = "proteins"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)
                
        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, (PeptideChain, Protein)):
                self._choices.extend([r.full_name() for r in ce.residues])
                        
    def select(self, names):
        '''
        Returns the atoms that matches a given list of peptide names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the residue names list.
        @type names: list
        '''
                        
        sel = set()

        if '*' in names:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)):
                    sel.update([at for at in ce.atom_list()])
        
        else:            
            vals = set([v.strip() for v in names])

            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce,(PeptideChain,Protein)):
                    for r in ce.residues:
                        resName = r.full_name().strip()
                        if resName in vals: 
                            sel.update([at for at in r.atom_list()])
                
        return sel
    
REGISTRY["residue_name"] = ResidueName
