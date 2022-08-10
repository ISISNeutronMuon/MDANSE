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
from MDANSE.Chemistry.ChemicalEntity import NucleotideChain, ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector

class NucleotideSugar(ISelector):

    section = "nucleic acids"

    def __init__(self, chemicalSystem: ChemicalSystem):

        ISelector.__init__(self,chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
            if isinstance(ce, NucleotideChain):
                self._choices.append(ce.name)


    def select(self, names):
        '''Returns the sugar atoms.
        
        Only for NucleotideChain objects.
        '''

        sel = set()

        if '*' in names:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, NucleotideChain):
                    sel.update([at for at in ce.sugars])
        else:            
            vals = set(names)
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, NucleotideChain) and ce.name in vals:
                    sel.update([at for at in ce.sugars])
            
        return sel
    
REGISTRY["nucleotide_sugar"] = NucleotideSugar
