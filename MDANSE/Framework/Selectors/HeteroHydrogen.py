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

from MDANSE.Framework.Selectors.ISelector import ISelector

class HeteroHydrogenBound(ISelector):
    
    type = "hetero_hydrogen"
    
    section = "hydrogens"

    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)

        for obj in self._universe.objectList():
                                        
            heteroatoms = [at for at in obj.atomList() if at.type.name.strip().lower() not in ['carbon','hydrogen']]
            
            for het in heteroatoms:
                neighbours = het.bondedTo()
                hydrogens = [neigh.fullName().strip().lower() for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen']
                self._choices.extend(sorted(hydrogens))

    def select(self, names):
    
        sel = set()

        if '*' in names:
            names = self._choices[1:]
            
        vals = set([v.lower() for v in names])
        sel.update([at for at in self._universe.atomList() if at.fullName().strip().lower() in vals])
        
        return sel
