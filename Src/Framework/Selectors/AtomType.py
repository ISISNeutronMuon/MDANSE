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

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector

class AtomType(ISelector):

    section = "atoms"

    def __init__(self, trajectory):

        ISelector.__init__(self,trajectory)
                
        self._choices.extend(sorted(set([at.type.name.lower() for at in self._universe.atomList()])))

    def select(self, elements):
        '''
        Returns the atoms that matches a given list of elements.
    
        @param universe: the universe
        @type universe: MMTK.universe
    
        @param elements: the atom elements list.
        @type elements: list
        '''
                
        sel = set()
                
        if '*' in elements:

            sel.update([at for at in self._universe.atomList()])
        
        else:
            
            vals = [v.lower() for v in elements]
                
            if "sulfur" in vals:
                vals.append("sulphur")
            else:                    
                if "sulphur" in vals:
                    vals.append("sulfur")
                
            vals = set(vals)
            
            sel.update([at for at in self._universe.atomList() if at.type.name.strip().lower() in vals])

        return sel

REGISTRY["atom_type"] = AtomType
