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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
    
class BooleanConfigurator(IConfigurator):
    """
    This Configurator allows to input a Boolean Value (True or False).
    """

    type = 'boolean'
    
    _default = False
    
    _shortCuts = {"true" : True, "yes" : True, "y" : True, "t" : True, "1" : True,
                  "false" : False, "no" : False, "n" : False, "f" : False, "0" : False}
    
    def configure(self, configuration, value):

        if hasattr(value,"lower"):
            
            value = value.lower()

            if not self._shortCuts.has_key(value):
                raise ConfiguratorError('invalid boolean string', self)
                        
        value = bool(value)
                        
        self['value'] = value

    def get_information(self):
        
        return "Value: %r" % self['value']