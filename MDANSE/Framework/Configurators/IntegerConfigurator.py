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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
    
class IntegerConfigurator(IConfigurator):
    """
    This Configurator allows to input an integer.
    """
    
    type = 'integer'
    
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: int or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: int or None
        :param choices: the list of integers allowed for the input value. If None, any value will be allowed.
        :type choices: int-list or None
        '''
        
        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        
        self._mini = int(mini) if mini is not None else None

        self._maxi = int(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []          
                
    def configure(self, configuration, value):
        '''
        Configure an integer value.
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the integer to be configured.
        :type value: int
        '''

        try:
            value = int(value)
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value < self._mini:
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value > self._maxi:
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value

    @property
    def mini(self):
        '''
        Returns the minimum value allowed for an input integer.
        
        :return: the minimum value allowed for an input value integer.
        :rtype: int or None
        '''
                        
        return self._mini

    @property
    def maxi(self):
        '''
        Returns the maximum value allowed for an input integer.
        
        :return: the maximum value allowed for an input value integer.
        :rtype: int or None
        '''
                
        return self._maxi

    @property
    def choices(self):
        '''
        Returns the list of integers allowed for an input float.
        
        :return: the choices allowed for an input float.
        :rtype: int-list or None
        '''
        
        return self._choices

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Value: %r" % self["value"]