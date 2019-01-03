# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/ResidueClass.py
# @brief     Implements module/class/test ResidueClass
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MMTK.Proteins import PeptideChain, Protein

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

# Dictionnary associating tuples of residue names (values) to their corresponding chemical family (key). 
CHEMFAMILIES = {'acidic'      : ('asp','glu'),
                'aliphatic'   : ('ile','leu','val'),
                'aromatic'    : ('his','phe','trp','tyr'),
                'basic'       : ('arg','his','lys'),
                'charged'     : ('arg','asp','glu','his','lys'),
                'hydrophobic' : ('ala','cys','cyx','gly','his','ile','leu','lys','met','phe','thr','trp','tyr','val'),
                'polar'       : ('arg','asn','asp','cys','gln','glu','his','lys','ser','thr','trp','tyr'),
                'small'       : ('ala','asn','asp','cys','cyx','gly','pro','ser','thr','val')}
                                         
class ResidueClass(ISelector):

    section = "proteins"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                        
        self._choices.extend(sorted(CHEMFAMILIES.keys()))

    def select(self, classes):
        '''
        Returns the atoms that matches a given list of peptide classes.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param classes: the residue classes list.
        @type classes: list
        '''
                
        sel = set()

        if '*' in classes:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:        
            vals = set([v.lower() for v in classes])
        
            selRes = set()
            for v in vals:
                if CHEMFAMILIES.has_key(v):
                    selRes.update(CHEMFAMILIES[v])
                                                                                 
            for obj in self._universe.objectList():
                try:        
                    res = obj.residues()
                    for r in res:
                        resName = r.symbol.strip().lower()
                        if resName in selRes:
                            sel.update([at for at in r.atomList()])
                except AttributeError:
                    pass
                                                   
        return sel
    
REGISTRY["residue_class"] = ResidueClass
