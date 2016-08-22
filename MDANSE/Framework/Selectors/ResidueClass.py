#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

from MMTK.Proteins import PeptideChain, Protein

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
                                         
class ResClass(ISelector):

    type = "residue_class"

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