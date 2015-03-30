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

import numpy

from Scientific.Geometry import Vector

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class VectorConfigurator(IConfigurator):
    """
    This Configurator allows to input a 3D vector, by giving its 3 components
    """
    
    type = "vector"
    
    _default = [1.0,0.0,0.0]
    
    def __init__(self, name, valueType=int, normalize=False, notNull=False, **kwargs):

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._valueType = valueType
        
        self._normalize = normalize
        
        self._notNull = notNull

    def configure(self, configuration, value):
                
        vector = Vector(numpy.array(value,dtype=self._valueType))

        if self._normalize:
            vector = vector.normal()
            
        if self._notNull:
            if vector.length() == 0.0:
                raise ConfiguratorError("The vector is null", self)

        self['vector'] = vector
        self['value'] = vector
        
    @property
    def valueType(self):
        
        return self._valueType

    @property
    def normalize(self):
        
        return self._normalize

    @property
    def notNull(self):
        
        return self._notNull

    def get_information(self):
        
        return "Value: %r" % self["value"]