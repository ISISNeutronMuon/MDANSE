# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideBase.py
# @brief     Implements module/class/test NucleotideBase
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

class Peptide(ISelector):

    section = "proteins"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, (PeptideChain,Protein)):
                self._choices.append(ce.name)


    def select(self, names):
        '''
        Returns the sugar atoms.
        
        Only for NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        if '*' in names:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)):
                    sel.update([at for at in ce.peptides])
        else:            
            vals = set(names)
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)) and ce.name in vals:
                    sel.update([at for at in ce.peptides])
            
        return sel
    
REGISTRY["peptide"] = Peptide
