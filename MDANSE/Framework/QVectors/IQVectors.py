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
import collections

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.UserDefinable import UserDefinable

class QVectorsError(Error):
    pass

class IQVectors(Configurable,UserDefinable):
    
    __metaclass__ = REGISTRY
    
    type = "q_vectors"

    is_lattice = False
            
    def __init__(self, trajectory):
        
        Configurable.__init__(self)
                
        UserDefinable.__init__(self,trajectory.filename)
                
        self._universe = trajectory.universe
        
    @abc.abstractmethod
    def generate(self, status=None):
        pass
    
    def setup(self,parameters):
        
        Configurable.setup(self, parameters)
        self._definition.clear()
        self._definition["generator"] = self.type
        self._definition["is_lattice"] = self.is_lattice
        self._definition["q_vectors"] = collections.OrderedDict()
        self._definition["parameters"] = parameters
        