# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ChainName.py
# @brief     Implements module/class/test ChainName
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MMTK.Proteins import PeptideChain, Protein

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class ChainName(ISelector):

    section = "proteins"

    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)
                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                self._choices.extend([c.name for c in obj])
        

    def select(self, names):
        '''
        Returns the atoms that matches a given list of chain names.
        
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the chain names list.
        @type names: list
        '''
        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                try:
                    sel.update([at for at in obj.atomList()])
                except AttributeError:
                    pass
        
        else:
            
            vals = set([v.lower() for v in names])
                
            for obj in self._universe.objectList():
                try:
                    for chain in obj:
                        chainName = chain.name.strip().lower()
                        if chainName in vals:
                            sel.update([at for at in chain.atomList()])
                except (AttributeError,TypeError):
                    continue
                
        return sel

REGISTRY["chain_name"] = ChainName
