# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/MoleculeIndex.py
# @brief     Implements module/class/test MoleculeIndex
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

class MoleculeIndex(ISelector):

    section = "molecules"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(list(range(len(self._universe.objectList()))))    

    def select(self, values):
        '''
        Returns the atoms that matches a given list of molecule indexes.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param indexes: the molecule indexes list.
        @type indexes: list
        '''
        
        sel = set()

        if '*' in values:

            sel.update([at for at in self._universe.atomList()])

        else:

            vals = set([int(v) for v in values])

            objList = self._universe.objectList()
        
            sel.update([at for v in vals for at in objList[v].atomList()])
        
        return sel

REGISTRY["molecule_index"] = MoleculeIndex
