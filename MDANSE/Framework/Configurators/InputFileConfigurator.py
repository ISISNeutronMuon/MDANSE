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

:author: Eric C. Pellegrini
'''

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class InputFileConfigurator(IConfigurator):
    """
    This Configurator allows to set an input file.    
    """
    
    type = 'input_file'
    
    _default = ""
    
    def __init__(self, name, wildcard="All files|*.*",**kwargs):
        '''
        Initializes the configurator object.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        '''
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._wildcard = wildcard
                
    def configure(self, configuration, value):
        '''
        Configure an input file. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input file.
        :type value: str 
        '''
                
        value = PLATFORM.get_path(value)
                
        if not os.path.exists(value):
            raise ConfiguratorError("the input file %r does not exist." % value, self)
        
        self["value"] = value 
        self["filename"] = value
            
    @property
    def wildcard(self):
        '''
        Returns the wildcard used to filter the input file.
        
        :return: the wildcard used to filter the input file.
        :rtype: str
        '''
        
        return self._wildcard

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Input file: %r" % self["value"]