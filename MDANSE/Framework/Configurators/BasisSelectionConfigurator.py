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

:author: Bachir Aoun and Eric C. Pellegrini
'''

from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule

class BasisSelection(IConfigurator):
    """
    This configurator allows to define a local basis per molecule. 
    
    For each molecule, the basis is defined using the coordinates of three atoms of the molecule. 
    These coordinates will respectively define the origin, the X axis and y axis of the basis, the 
    Z axis being latter defined in such a way that the basis is direct.     
    """
    
    type = 'basis_selection'
    
    _default = None

    def configure(self, configuration, value):
        '''
        Configure an input value. 
        
        The value can be:
        
        #. a dict with *'molecule'*, *'origin'*, *'x_axis'* and *'y_axis'* keys. *'molecule'* key is \
        the name of the molecule for which the axis selection will be performed and *'origin'*, *'x_axis'* and *'y_axis'* \
        keys are the names of three atoms of the molecule that will be used to define respectively the origin, the X and Y axis of the basis  
        #. str: the axis selection will be performed by reading the corresponding user definition.
        
        :param configuration: the current configuration
        :type configuration: MDANSE.Framework.Configurable.Configurable
        :param value: the input value
        :type value: tuple or str 

        :note: this configurator depends on 'trajectory' configurator to be configured
        '''

        trajConfig = configuration[self._dependencies['trajectory']]
            
        if UD_STORE.has_definition(trajConfig["basename"],"basis_selection",value): 
            ud = UD_STORE.get_definition(trajConfig["basename"],"basis_selection",value)
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
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Basis vector:%s" % self["value"]