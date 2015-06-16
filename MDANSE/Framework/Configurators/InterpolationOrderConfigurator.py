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

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator
            
class InterpolationOrderConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to input the interpolation order to be applied when deriving velocities from atomic coordinates.

    The allowed value are *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*, the 
    former one will not interpolate the velocities from atomic coordinates but will directly use the velocities stored in the trajectory file.
    
    :attention: it is of paramount importance for the trajectory to be sampled with a very low time \
    step to get accurate velocities interpolated from atomic coordinates. 

    :note: this configurator depends on 'trajectory' configurator to be configured.
    """
    
    type = "interpolation_order"
    
    _default = "no interpolation"
    
    orders = ["no interpolation","1st order","2nd order","3rd order","4th order","5th order"] 
    
    def __init__(self, name, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str.
        '''
                
        SingleChoiceConfigurator.__init__(self, name, choices=InterpolationOrderConfigurator.orders, **kwargs)

    def configure(self, configuration, value):
        '''
        Configure the input interpolation order.
                
        :param configuration: the current configuration.
        :type configuration: MDANSE.Framework.Configurable.Configurable
        :param value: the interpolation order to be configured.
        :type value: str one of *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*.
        '''
        
        SingleChoiceConfigurator.configure(self, configuration, value)
        
        if value == "no interpolation":

            trajConfig = configuration[self._dependencies['trajectory']]

            if not "velocities" in trajConfig['instance'].variables():
                raise ConfiguratorError("the trajectory does not contain any velocities. Use an interpolation order higher than 0", self)
            
            self["variable"] = "velocities"
            
        else:

            self["variable"] = "configuration"