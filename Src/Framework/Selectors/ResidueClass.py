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
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import PeptideChain, Protein, ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector

# Dictionnary associating tuples of residue names (values) to their corresponding chemical family (key). 
CHEMFAMILIES = {'acidic'      : ('ASP','GLU'),
                'aliphatic'   : ('ILE','LEU','VAL'),
                'aromatic'    : ('HIS','PHE','TRP','TYR'),
                'basic'       : ('ARG','HIS','LYS'),
                'charged'     : ('ARG','ASP','GLU','HIS','LYS'),
                'hydrophobic' : ('ALA','CYS','CYX','GLY','HIS','HID','HIP','HIE','ILE','LEU','LYS','MET','PHE','THR','TRP','TYR','VAL'),
                'polar'       : ('ARG','ASN','ASP','CYS','GLN','GLU','HIS','LYS','SER','THR','TRP','TYR'),
                'small'       : ('ALA','ASN','ASP','CYS','CYX','GLY','PRO','SER','THR','VAL')}
                                         
class ResidueClass(ISelector):

    section = "proteins"

    def __init__(self, chemicalSystem: ChemicalSystem):

        ISelector.__init__(self,chemicalSystem)
                        
        self._choices.extend(sorted(CHEMFAMILIES.keys()))

    def select(self, classes):
        '''Returns the atoms that matches a given list of peptide classes.
        
        @param classes: the residue classes list.
        @type classes: list
        '''
                
        sel = set()

        if '*' in classes:
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce, (PeptideChain,Protein)):
                    sel.update([at for at in ce.atom_list])
        
        else:        
            vals = set(classes)
        
            selRes = set()
            for v in vals:
                if v in CHEMFAMILIES:
                    selRes.update(CHEMFAMILIES[v])
            
            for ce in self._chemicalSystem.chemical_entities:
                if isinstance(ce,(PeptideChain,Protein)):
                    res = ce.residues
                    for r in res:
                        resName = r.code.strip()
                        if resName in selRes:
                            sel.update([at for at in r.atom_list])
                                                   
        return sel
    
REGISTRY["residue_class"] = ResidueClass
