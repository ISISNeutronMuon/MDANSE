'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

from MDANSE.Core.Error import Error

class ConfigurationError(Error):
    pass

import collections

class Configurable(object):
    
    configurators = collections.OrderedDict()

    def __init__(self):
        
        self._configuration = {}
        
        self._configured=False
        
    def __getitem__(self, name):
        """
        Returns a configuration item given its name
        If not found raise a ConfigurationError. 
        """
        
        if self._configurators.has_key(name):
            return self._configuration.setdefault(name,{})
        
        raise ConfigurationError("The item %r is not valid for this configuration." % name)
        
    def setup(self,parameters):
        """
        Setup the configuration given a set of parameters
        """
                
        self._configuration.clear()

        self._configured=False
                
        # If no configurator has to be configured, just return
        if not self.configurators:
            return
        
        if isinstance(parameters,dict):
            for k,v in self.configurators.items():
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
        
        if not self._configured:
            return "Not yet configured"
        
        info = []
        
        for configurator in self._configuration:
            
            info.append(configurator.get_information())
            
        return "\n".join(info)