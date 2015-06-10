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
Created on Mar 30, 2015

@author: pellegrini
'''

import abc

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Status import Status

class QVectorsError(Error):
    pass

class IQVectors(Configurable):
    
    __metaclass__ = REGISTRY
    
    type = "q_vectors"

    is_lattice = False
            
    def __init__(self, trajectory, status=False):
        
        Configurable.__init__(self)
                                
        self._universe = trajectory.universe
        
        if status:
            self._status = Status()
        else:
            self._status = None
            
    @abc.abstractmethod
    def _generate(self):
        pass
    
    def generate(self):
        
        self._generate()

        if self._status is not None:
            self._status.finish()        
        
        