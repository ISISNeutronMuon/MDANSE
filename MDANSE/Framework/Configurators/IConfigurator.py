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

class ConfiguratorError(Error):
    
    def __init__(self, message, configurator=None):

        self._message = message
        self._configurator = configurator
                
    def __str__(self):
        
        if self._configurator is not None:
            self._message = "Configurator: %r --> %s" % (self._configurator.name,self._message)
        
        return self._message
    
    @property
    def configurator(self):
        return self._configurator
                                                
class IConfigurator(dict):
    
    __metaclass__ = REGISTRY

    type = "configurator"
    
    _default = None
    
    _doc_ = "undocumented"
                            
    def __init__(self, name, dependencies=None, default=None, label=None, widget=None):

        self._name = name
        
        self._dependencies = dependencies if dependencies is not None else {}

        self._default = default if default is not None else self.__class__._default

        self._label = label if label is not None else " ".join(name.split('_')).strip()

        self._widget = widget if widget is not None else self.type
            
    @property
    def default(self):
        
        return self._default
    
    @property
    def dependencies(self):
        
        return self._dependencies
        
    @property
    def label(self):
        
        return self._label

    @property
    def name(self):
        
        return self._name

    @property
    def widget(self):
        
        return self._widget
    
    @abc.abstractmethod
    def configure(self, configuration, value):
        pass
                        
    def add_dependency(self, name, conf):
        
        if self._dependencies.has_key(name):
            raise ConfiguratorError("duplicate dependendy for configurator %s" % name, self)
                        
    def check_dependencies(self, configured):
        
        for c in self._dependencies.values():
            if c not in configured:
                return False

        return True
    
    @abc.abstractmethod
    def get_information(self):
        pass