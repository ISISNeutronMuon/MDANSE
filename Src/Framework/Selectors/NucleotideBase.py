# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/NucleotideBase.py
# @brief     Implements module/class/test NucleotideBase
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class NucleotideBase(ISelector):

    section = "nucleic acids"

    def select(self, *args):
        '''
        Returns the bases atoms.
        
        Only for NucleotideChain objects.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():
            try:
                sel.update([at for at in obj.bases().atomList()])
            except AttributeError:
                pass
            
        return sel
    
REGISTRY["nucleotide_base"] = NucleotideBase
