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

@author: pellegrini
'''

from MMTK.Proteins import PeptideChain, Protein

from MDANSE.Framework.Selectors.ISelector import ISelector

class ResidueName(ISelector):

    type = "residue_name"

    section = "proteins"

    def __init__(self, universe):

        ISelector.__init__(self,universe)
                
        for obj in self._universe.objectList():
            if isinstance(obj, (PeptideChain, Protein)):
                for chain in obj:
                    self._choices.extend([r.fullName() for r in chain.residues()])
                        
    def select(self, names):
        '''
        Returns the atoms that matches a given list of peptide names.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param names: the residue names list.
        @type names: list
        '''
                        
        sel = set()

        if '*' in names:
            for obj in self._universe.objectList():
                if isinstance(obj, (PeptideChain,Protein)):
                    sel.update([at for at in obj.atomList()])
        
        else:            
            vals = set([v.strip().lower() for v in names])

            for obj in self._universe.objectList():
                try:
                    for r in obj.residues():
                        resName = r.fullName().strip().lower()
                        if resName in vals: 
                            sel.update([at for at in r.atomList()])
                except:
                    pass
                
        return sel