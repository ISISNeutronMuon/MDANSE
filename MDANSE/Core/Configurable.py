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

import collections

from MDANSE.Core.Error import Error

class ConfigurationError(Error):
    '''
    Handles the exception that may occurs when configuring an object that derives from MDANSE.Core.Configurable class.
    '''
    pass

class Configurable(object):
    '''
    This class allows any object that derives from it to be configurable within the MDANSE framework.
    
    Within that framework, the object will also have to define the class attribute 'configurators' as 
    a MDANSE.Framework.Configurators.ConfiguratorsDict object to complete its configuration.    
    '''
    
    configurators = collections.OrderedDict()

    def __init__(self):
        '''
        Constructor
        '''
        
        self._configuration = {}
        
        self._configured=False
        
    def __getitem__(self, name):
        """
        Returns a configuration item given its name.
        
        :param name: the name of the configuration item
        :type name: str 
        
        If not found raise a ConfigurationError. 
        """
        
        if not self.configurators.has_key(name):
            raise ConfigurationError("The item %r is not valid for this configuration." % name)
        
        return self._configuration.setdefault(name,{})
        
    def setup(self,parameters):
        '''
        Setup the configuration according to a set of input parameters.
        
        :param parameters: the input parameters
        :type parameters: dict
        '''
                
        # Cleans the previous configuration
        self._configuration.clear()

        self._configured=False
                
        # If no configurator has to be configured, just return
        if not self.configurators:
            self._configured=True
            return
        
        if isinstance(parameters,dict):
            # Loop over the configuration items          
            for k,v in self.configurators.items():
                # If no input parameter has been set for this item, use its default value.
                if not parameters.has_key(k):
                    parameters[k] = v.default
        else:
            raise ConfigurationError("Invalid type for configuration parameters")             
                        
        toBeConfigured = set(self.configurators.keys())
        configured = set()
                
        while toBeConfigured != configured:
            
            progress = False

            for name,conf in self.configurators.items():
                                                                                
                if name in configured:
                    continue
                
                if conf.check_dependencies(configured):

                    conf.configure(self,parameters[name])
                    
                    self._configuration[name]=conf
                                                            
                    configured.add(name)
                    
                    progress = True
                    
            if not progress:
                raise ConfigurationError("Circular or unsatisfiable dependencies when setting up configuration.")

        self._configured=True

    def __str__(self):
        '''
        Returns the informations about the current configuration in text form.
        
        :return: the informations about the current configuration in text form
        :rtype: str
        '''
        
        if not self._configured:
            return "Not yet configured"
        
        info = []
        
        for configurator in self._configuration.values():
            
            info.append(configurator.get_information())
            
        return "\n".join(info)