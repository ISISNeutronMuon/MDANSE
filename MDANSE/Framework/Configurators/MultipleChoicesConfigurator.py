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

class MultipleChoicesConfigurator(IConfigurator):
    """
     This Configurator allows to select several items among multiple choices.
    """
    
    type = "multiple_choices"
    
    _default = []
            
    def __init__(self, name, choices=None, nChoices=None, **kwargs):
        
        IConfigurator.__init__(self, name, **kwargs)
        
        self._choices = choices if choices is not None else []
        
        self._nChoices = nChoices

    def configure(self, configuration, value):

        if self._nChoices is not None:
            if len(value) != self._nChoices:
                raise ConfiguratorError("invalid number of choices.", self)

        indexes = []
        for v in value:
            try:
                indexes.append(self._choices.index(v))
            except ValueError:                        
                raise ConfiguratorError("%r item is not a valid choice" % v, self)
            
        self["indexes"] = indexes
        self["choices"] = [self._choices[i] for i in indexes]
        self["value"] = self["choices"]
            
    @property
    def choices(self):
        
        return self._choices
    
    @property
    def nChoices(self):
        
        return self._nChoices

    def get_information(self):
        
        return "Selected items: %r" % self['choices']