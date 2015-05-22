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
Created on May 22, 2015

@author: pellegrini
'''

import ast

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
 
class StringConfigurator(IConfigurator):
    """
    This Configurator allows to input a string.
    """
    
    type = 'string'
    
    _default = ""

    def __init__(self, name, evalType=None, acceptNullString=True, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param evalType: the type to which the string will be evaluated or None if it is let as is.
        :type evalType: python object or None
        :param acceptNullString: if True a null (or blank) string can be input.
        :type acceptNullString: bool
        '''
        
        IConfigurator.__init__(self, name, **kwargs)
        
        self._evalType = evalType
        
        self._acceptNullString = acceptNullString
    
    def configure(self, configuration, value):
        '''
        Configure an input string.
                
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input string
        :type value: str
        '''

        value = str(value)
        
        if not self._acceptNullString:
            if not value.strip():
                raise ConfiguratorError("invalid null string", self)
            
        if self._evalType is not None:
            value = ast.literal_eval(value)
            if not isinstance(value,self._evalType):
                raise ConfiguratorError("the string can not be eval to %r type" % self._evalType.__name__, self)
                        
        self['value'] = value
        
    @property
    def acceptNullString(self):
        '''
        Returns whether or not a null (or blank) string is accepted.
        
        :return: True if a null (or blank) string is accepted as input, False otherwise.
        :rtype: bool
        '''
        
        return self._acceptNullString
    
    @property
    def evalType(self):
        '''
        Returns the type to which the string will be evaluated or None if it is let as is.

        :return: the type to which the string will be evaluated or None if it is let as is.
        :rtype: python object or None
        '''
        
        return self._evalType
    
    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Value: %r" % self['value']