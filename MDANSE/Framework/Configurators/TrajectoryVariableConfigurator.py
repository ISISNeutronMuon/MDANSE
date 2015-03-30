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
          
class TrajectoryVariableConfigurator(IConfigurator):
    """
    This configurator allows to get a variable stored in a MMTK trajectory
    """
        
    type = 'trajectory_variable'
    
    _default = "velocities"
        
    def configure(self, configuration, value):
                
        trajConfig = configuration[self._dependencies['trajectory']]
       
        if not value in trajConfig['instance'].variables():
            raise ConfiguratorError("%r is not registered as a trajectory variable." % value, self)
        
        self['value'] = value

    def get_information(self):
        
        return "Selected variable: %r" % self["value"]