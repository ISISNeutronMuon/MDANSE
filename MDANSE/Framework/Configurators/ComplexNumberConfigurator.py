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

from MDANSE.Mathematics.Arithmetic import ComplexNumber
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class ComplexNumberConfigurator(IConfigurator):
    """
    This Configurator allows to input a Complex Value a + bi, 
    where a and b are real numbers and i is the imaginary unit.
    """
    
    type = 'complex_number'
    
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._mini = ComplexNumber(mini) if mini is not None else None

        self._maxi = ComplexNumber(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []
                    
    def configure(self, configuration, value):
        
        value = ComplexNumber(value)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value.modulus() < self._mini.modulus():
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value.modulus() > self._maxi.modulus():
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value
        
    @property
    def mini(self):
        
        return self._mini

    @property
    def maxi(self):
        
        return self._maxi

    @property
    def choices(self):
        
        return self._choices

    def get_information(self):
        
        return "Value: %r" % self['value']