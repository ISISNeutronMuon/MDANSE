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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class SingleChoiceConfigurator(IConfigurator):
    """
     This Configurator allows to select a single item among multiple choices.
    """
    
    type = "single_choice"
    
    _default = []
            
    def __init__(self, name, choices=None, **kwargs):
        '''
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        '''
        
        IConfigurator.__init__(self, name, **kwargs)
        
        self._choices = choices if choices is not None else []

    def configure(self, value):
        '''
        Configure the input item.
                
        :param value: the input selection list.
        :type value: list
        '''

        try:
            self["index"] = self._choices.index(value)
        except ValueError:                        
            raise ConfiguratorError("%r item is not a valid choice" % value, self)
        else:        
            self["value"] = value
            
    @property
    def choices(self):
        '''
        Returns the list of allowed selection items.
        
        :return: the list of allowed selection items.
        :rtype: list
        '''
        
        return self._choices

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        return "Selected item: %r" % self['value']