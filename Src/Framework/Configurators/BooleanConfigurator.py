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

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
    
class BooleanConfigurator(IConfigurator):
    """
    This Configurator allows to input a Boolean Value (True or False).
    
    The input value can be directly provided as a Python boolean or by the using the following (standard)
     representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
    """
    
    _default = False
    
    _shortCuts = {True  : True, "true"  : True , "yes" : True, "y" : True, "1" : True, 1 : True,
                  False : False, "false" : False, "no"  : False, "n" : False, "0" : False, 0 : False}
    
    def configure(self, value):
        '''
        Configure an input value. 
        
        The value must be one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0.
        
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input value
        :type value: one of True/False, 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
        '''

        if not self._shortCuts.has_key(value):
            raise ConfiguratorError('the input value can not be interpreted as a boolean', self)
                        
        self["value"] = self._shortCuts[value]
                                                
    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Value: %r" % self['value']
    
REGISTRY["boolean"] = BooleanConfigurator
