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
Created on Jun 9, 2015

@author: Eric C. Pellegrini
'''

import os

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator,ConfiguratorError
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

class PartialChargeConfigurator(IConfigurator):
    """
    This configurator allows to input partial charges.
    """
    
    type = 'partial_charges'
    
    _default = ''
                   
    def configure(self, configuration, value):
        '''
        Configure a python script. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the python script.
        :type value: str 
        '''

        trajConfig = configuration[self._dependencies['trajectory']]
        
        if UD_STORE.has_definition(trajConfig["basename"],'partial_charges',value):
            self['charges'] = UD_STORE[trajConfig["basename"],'partial_charges',value]
        else:
            if isinstance(value,basestring):                
                # Case of a python script
                if os.path.exists(value):
                    namespace = {}
                    
                    execfile(value,self.__dict__,namespace)
                            
                    if not namespace.has_key('charges'):
                        raise ConfiguratorError("The variable 'charges' is not defined in the %r python script file" % (self["value"],))
                        
                    self.update(namespace)
                else:
                    raise ConfiguratorError("The python script defining partial charges %s could not be found." % value)
                    
            elif isinstance(value,dict):
                self['charges'] = value
            else:
                raise ConfiguratorError("Invalid type for partial charges.")
                
            
    def get_information(self):
        '''
        Returns some basic informations about the partial charges.
        
        :return: the informations about the partial charges.
        :rtype: str
        '''
        
        info = 'Sum of partial charges = %8.3f' % sum(self['charges'].values())
        
        return info
