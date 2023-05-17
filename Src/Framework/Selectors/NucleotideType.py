# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideType.py
# @brief     Implements module/class/test NucleotideType
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import NucleotideChain
from MDANSE.Framework.Selectors.ISelector import ISelector
                                         
class NucleotideType(ISelector):

    section = "nucleic acids"

    def __init__(self, chemicalSystem):

        ISelector.__init__(self,chemicalSystem)

        types = set()                
        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, NucleotideChain):
                types.update([n.code.strip() for n in ce.nucleotides])
        self._choices.extend(sorted(types))


    def select(self, types):
        '''Returns the atoms that matches a given list of nucleotide types.
        
        @param types: the nucleotide types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, NucleotideChain):
                    sel.update([at for at in ce.atom_list()])
        
        else:
            vals = set([v for v in types])

            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, NucleotideChain):
                    for nucl in ce.nucleotides:
                        nuclType = nucl.code.strip()
                        if nuclType in vals:
                            sel.update([at for at in nucl.atom_list()])
                
        return sel

REGISTRY["nucleotide_type"] = NucleotideType
