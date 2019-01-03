# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideType.py
# @brief     Implements module/class/test NucleotideType
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MMTK.NucleicAcids import NucleotideChain

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                                         
class NucleotideType(ISelector):

    section = "nucleic acids"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        for obj in self._universe.objectList():
            if isinstance(obj, NucleotideChain):
                self._choices.extend([r.symbol.strip().lower() for r in obj.residues()])
                

    def select(self, types):
        '''
        Returns the atoms that matches a given list of nucleotide types.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param types: the nucleotide types list.
        @type types: list
        '''
        
        sel = set()

        if '*' in types:
            for obj in self._universe.objectList():
                if isinstance(obj, NucleotideChain):
                    sel.update([at for at in obj.atomList()])
        
        else:
            vals = set([v.lower() for v in types])

            for obj in self._universe.objectList():
                try:
                    res = obj.residues()
                    for nucl in res:
                        nuclType = nucl.symbol.strip().lower()
                        if nuclType in vals:
                            sel.update([at for at in nucl.atomList()])
                except AttributeError:
                    pass
                
        return sel

REGISTRY["nucleotide_type"] = NucleotideType
