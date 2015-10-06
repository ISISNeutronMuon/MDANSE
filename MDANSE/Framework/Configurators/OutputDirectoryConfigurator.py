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
Created on May 21, 2015

:author: Eric C. Pellegrini
'''

import os

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
        
class OutputDirectoryConfigurator(IConfigurator):
    """
     This Configurator allows to set an output directory.
    """
    
    type = "output_directory"
    
    _default = os.getcwd()

    def __init__(self, name, new=False, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param new: if True the output directory path will be checked for being new. 
        :type new: bool
        '''        
                
        IConfigurator.__init__(self, name, **kwargs)
        
        self._new = new

    def configure(self, value):
        '''
        Configure an output directory. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the output directory.
        :type value: str 
        '''
        
        value = PLATFORM.get_path(value)
        
        if self._new:
            if os.path.exists(value):
                raise ConfiguratorError("the output directory must not exist", self)
                                                
        self['value'] = value        
            
    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Output directory: %r" % self['value']