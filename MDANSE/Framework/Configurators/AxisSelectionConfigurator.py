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

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule
        
class AxisSelection(IConfigurator):
    """
    This configurator allows to define a local axis per molecule. 
    
    For each molecule, the axis is defined using the coordinates of two atoms of the molecule. 
    
    :note: this configurator depends on 'trajectory' configurator to be configured.
    """
        
    _default = None

    def configure(self, value):
        '''
        Configure an input value. 
        
        The value can be:
        
        #. a dict with *'molecule'*, *'endpoint1'* and *'endpoint2'* keys. *'molecule'* key \
        is the name of the molecule for which the axis selection will be performed and *'endpoint1'* \
        and *'endpoint2'* keys are the names of two atoms of the molecule along which the axis will be defined  
        #. str: the axis selection will be performed by reading the corresponding user definition.
        
        :param configuration: the current configuration
        :type configuration: MDANSE.Framework.Configurable.Configurable
        :param value: the input value
        :type value: tuple or str 
        '''
        
        trajConfig = self._configurable[self._dependencies['trajectory']]
                
        if UD_STORE.has_definition(trajConfig["basename"],"axis_selection",value): 
            ud = UD_STORE.get_definition(trajConfig["basename"],"axis_selection",value)
            self.update(ud)
        else:
            self.update(value)

        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint1'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint2'], True)

        self["value"] = value
          
        self['endpoints'] = zip(e1,e2)      
        
        self['n_axis'] = len(self['endpoints'])

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Axis vector:%s" % self["value"]
    
REGISTRY["axis_selection"] = AxisSelection
    