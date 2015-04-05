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

from MDANSE.Framework.UserDefinables.UserDefinitions import USER_DEFINITIONS
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule

class BasisSelection(IConfigurator):
    """
    This configurator allow to select a basis selection among the User Definitions.
    This could be mandatory for the analysis, if not, some generic behavior will be setup.
    An axis selection is defined using :
    - one origin, 
    - two vector define using the origin and two atomic coordinates (or atomic cluster center of mass),
    - the third direction, automatically taken as the vector product of the two precedent.  
    
    To Build a basis selection definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Basis selection" plugin
    """
    
    type = 'basis_selection'
    
    _default = None

    def configure(self, configuration, value):
        trajConfig = configuration[self._dependencies['trajectory']]

        ud = USER_DEFINITIONS.get(trajConfig["basename"],"basis_selection",value)        
        if ud is not None:
            self.update(ud)
        else:
            self.update(value)
                
        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['origin'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['x_axis'], True)
        e3 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['y_axis'], True)
        
        self["value"] = value
        
        self['basis'] = zip(e1,e2,e3)      
        
        self['n_basis'] = len(self['basis'])

    def get_information(self):
        
        return "Basis vector:%s" % self["value"]