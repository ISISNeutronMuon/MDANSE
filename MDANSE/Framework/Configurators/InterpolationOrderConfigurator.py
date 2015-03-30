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

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator
from MDANSE.Mathematics.Signal import INTERPOLATION_ORDER
            
class InterpolationOrderConfigurator(IntegerConfigurator):
    """
    This configurator allows to set as input the order of the interpolation apply when deriving velocities 
    from atomic coordinates to the atomic trajectories.
    The value should be higher than 0 if velocities are not provided with the trajectory.
    """
    
    type = "interpolation_order"
    
    _default = 0

    def __init__(self, name, **kwargs):
                
        IntegerConfigurator.__init__(self, name, choices=range(-1,len(INTERPOLATION_ORDER)), **kwargs)

    def configure(self, configuration, value):
        
        IntegerConfigurator.configure(self, configuration, value)
        
        if value == -1:

            trajConfig = configuration[self._dependencies['trajectory']]

            if not "velocities" in trajConfig['instance'].variables():
                raise ConfiguratorError("the trajectory does not contain any velocities. Use an interpolation order higher than 0", self)
            
            self["variable"] = "velocities"
            
        else:

            self["variable"] = "configuration"
            
    def get_information(self):
        
        if self["value"] == -1:
            return "No velocities interpolation"
        else:
            return "Velocities interpolated from atomic coordinates"