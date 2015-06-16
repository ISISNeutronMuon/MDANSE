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

:author: Eric C. Pellegrini
'''

import ast

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
        
class PythonObjectConfigurator(IConfigurator):
    """
    This Configurator allows to input and evaluate basic python object.
    
    The python object supported are strings, numbers, tuples, lists, dicts, booleans and None type.
    
    :note: this configurator is based on a literal and safe evaluation of the input using ast standard library module.
    """
    
    type = 'python_object'
    
    _default = '""'

    def configure(self, configuration, value):
        '''
        Configure a python object. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the python object to be configured and evaluated.
        :type value: strings, numbers, tuples, lists, dicts, booleans or None type.
        '''
        
        value = ast.literal_eval(repr(value))
                                
        self['value'] = value

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Python object: %r" % self['value']