# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideName.py
# @brief     Implements module/class/test NucleotideName
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
    
class NucleotideName(ISelector):

    section = "nucleic acids"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)

        for obj in self._universe.objectList():
            if isinstance(obj, NucleotideChain):
                self._choices.extend([r.fullName() for r in obj.residues()])
        

    def select(self, names):
        '''
        Returns the atoms that matches a given list of nucleotide names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the nucletodide names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                if isinstance(obj, NucleotideChain):
                    sel.update([at for at in obj.atomList()])
        
        else:
            vals = set([v.lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    res = obj.residues()
                    for nucl in res:
                        nuclName = nucl.fullName().strip().lower()
                        if nuclName in vals:
                            sel.update([at for at in nucl.atomList()])
                except AttributeError:
                    pass
                       
        return sel
    
REGISTRY["nucleotide_name"] = NucleotideName
