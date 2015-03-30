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

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class InputFileConfigurator(IConfigurator):
    """
    This Configurator allows to set as input any existing file.
    """
    
    type = 'input_file'
    
    _default = ""
    
    def __init__(self, name, checkExistence=True, wildcard="All files|*.*", **kwargs):
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._checkExistence = checkExistence
        
        self._wildcard = wildcard
                
    def configure(self, configuration, value):
        if self.checkExistence:
            value = PLATFORM.get_path(value)
                    
            if not os.path.exists(value):
                raise ConfiguratorError("the input file %r does not exist." % value, self)
        
        self["value"] = value 
        self["filename"] = value
        
    @property
    def checkExistence(self):
        
        return self._checkExistence
    
    @property
    def wildcard(self):
        
        return self._wildcard

    def get_information(self):
        
        return "Input file: %r" % self["value"]