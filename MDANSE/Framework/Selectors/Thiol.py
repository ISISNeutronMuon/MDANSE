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
    
class Thiol(ISelector):

    section = "chemical groups"

    def select(self, *args):
        '''
        Returns the thiol atoms.

        @param universe: the universe
        @type universe: MMTK.universe
        '''

        sel = set()

        for obj in self._universe.objectList():

            sulphurs = [at for at in obj.atomList() if at.type.name.strip().lower() in ['sulphur', 'sulfur']]
            for sul in sulphurs:
                neighbours = sul.bondedTo()
                if not neighbours:
                    neighbours = self._universe.selectShell(sul,r1=0.0,r2=0.11)
                hydrogens = [neigh for neigh in neighbours if neigh.type.name.strip().lower() == 'hydrogen'] 
                if len(hydrogens)==1:
                    sel.update([sul] + hydrogens)
                
        return sel
    
REGISTRY["thiol"] = Thiol
