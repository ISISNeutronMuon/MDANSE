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

from MDANSE import USER_DEFINITIONS
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule
        
class AxisSelection(IConfigurator):
    """
    This configurator allow to select  an axis selection among the User Definitions.
    This could be mandatory for the analysis, if not, some generic behavior will be setup.
    An axis selection is defined using two atomic coordinates (or atomic cluster center of mass) 
    
    To Build an axis selection definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Axis selection" plugin
    """
    
    type = "axis_selection"
    
    _default = None

    def configure(self, configuration, value):
        
        trajConfig = configuration[self._dependencies['trajectory']]
                
        target = trajConfig["basename"]

        if USER_DEFINITIONS.has_key(value):
            definition = USER_DEFINITIONS.check_and_get(target, "axis_selection", value)
            self.update(definition)
        else:
            self.update(value)

        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint1'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint2'], True)

        self["value"] = value
          
        self['endpoints'] = zip(e1,e2)      
        
        self['n_axis'] = len(self['endpoints'])

    def get_information(self):
        
        return "Axis vector:%s" % self["value"]