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

@author: Eric C. Pellegrini
'''

import abc

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class ConfiguratorError(Error):
    '''
    This class handles any exception related to Configurator-derived object
    '''
    
    def __init__(self, message, configurator=None):
        '''
        Initializes the the object.
        
        :param message: the exception message
        :type message: str
        :param configurator: the configurator in which the exception was raised
        :type configurator: an instance or derived instance of a MDANSE.Framework.Configurators.Configurator object
        '''

        self._message = message
        self._configurator = configurator
                
    def __str__(self):
        '''
        Returns the informal string representation of this object.
        
        :return: the informal string representation of this object
        :rtype: str
        '''
        
        if self._configurator is not None:
            self._message = "Configurator: %r --> %s" % (self._configurator.name,self._message)
        
        return self._message
    
    @property
    def configurator(self):
        '''
        Returns the configurator in which the exception was raised

        :return: the configurator in which the exception was raised
        :rtype: an instance or derived instance of a MDANSE.Framework.Configurators.Configurator object
        '''
        return self._configurator
                                                
class IConfigurator(dict):
    '''
    This class implements the base class for configurator objects. A configurator object is a dictionary-derived object that is used 
    to configure one item of a given configuration. Once the input value given for that item is configured, the dictionary is updated 
    with keys/values providing information about this item.
    
    A configurator is not designed to be used as a stand-alone object. It should be used within the scope of a Configurable object that 
    will store a complete configuration for a given task (e.g. job, Q vectors, instrument resolution ...).
    
    Usually, configurator objects are self-consistent but for complex ones, it can happen that they depends on other configurators of the 
    configuration.
    '''
    
    __metaclass__ = REGISTRY

    type = "configurator"
    
    _default = None
    
    _doc_ = "undocumented"
                            
    def __init__(self, name, dependencies=None, default=None, label=None, widget=None):
        '''
        Initializes a configurator object.
        
        :param name: the name of this configurator.
        :type name: str
        :param dependencies: the other configurators on which this configurator depends on to be configured. This has to be input as a 
        dictionary that maps the name under which the dependency will be used within the configurator implementation to the actual name 
        of the configurator on which this configurator is depending on.  
        :type dependencies: (str,str)-dict
        :param default: the default value of this configurator.
        :type default: any python object
        :param label: the label of the panel in which this configurator will be inserted in the MDANSE GUI.
        :type label: str
        :param widget: the configurator widget that corresponds to this configurator.
        :type widget: str
        '''

        self._name = name
                
        self._dependencies = dependencies if dependencies is not None else {}

        self._default = default if default is not None else self.__class__._default

        self._label = label if label is not None else " ".join(name.split('_')).strip()

        self._widget = widget if widget is not None else self.type
            
    @property
    def default(self):
        '''
        Returns the default value of this configurator.
        
        :return: the default value of this configurator.
        :rtype: any Python object
        '''
        
        return self._default
    
    @property
    def dependencies(self):
        '''
        Returns the dependencies maps of this configurator.
        
        :return: the dependencies maps of this configurator.
        :rtype: (str,str)-dict
        '''
        
        return self._dependencies
        
    @property
    def label(self):
        '''
        Returns the label of this configurator that will be used when inserting its corresponding widget in a configuration panel.
        
        :return: the label of this configurator.
        :rtype: str 
        '''
        
        return self._label

    @property
    def name(self):
        '''
        Returns the name of this configurator. That name will be used as a key of a Configurable object.
        
        :return: the name of this configurator.
        :rtype: str
        '''
        
        return self._name

    @property
    def widget(self):
        '''
        Returns the name of the widget that will be associated to this configurator.
        
        :return: the name of the configurator-widget.
        :rtype: str
        '''
        
        return self._widget
    
    @abc.abstractmethod
    def configure(self, configuration, value):
        '''
        Configures this configurator with a given value.
        
        :param configuration: the current configuration. The configuration is passed at configuration time because it can be used in the case where
        the configurator depends on other configurators to be comfigured.
        :type configuration: Framework.Configurable.Configurable object
        :param value: the input value to be configured.
        :type value: depends on the configurator

        :note: this is an abstract method.
        '''
                                                
    def check_dependencies(self, configured):
        '''
        Check that the configurators on which this configurator depends on have already been configured.
        
        :param configured: the names of the configurators that have already been configured when configuring this configurator.
        :type: list of str
        
        :return: True if the configurators on which this configurator depends on have already been configured. False otherwise.
        :rtype: bool
        '''
        
        for c in self._dependencies.values():
            if c not in configured:
                return False

        return True
    
    @abc.abstractmethod
    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        
        :note: this is an abstract method.
        '''

        pass