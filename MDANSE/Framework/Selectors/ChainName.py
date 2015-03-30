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

class ChainName(ISelector):

    type = "chainname"

    section = "proteins"

    def __init__(self, universe):
        
        ISelector.__init__(self,universe)
                
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
                except AttributeError:
                    pass
                
        return sel