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

from MDANSE import ELEMENTS
from MDANSE.Framework.UserDefinables.UserDefinitions import USER_DEFINITIONS
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
from MDANSE.Framework.Selectors.SelectionParser import SelectionParser
        
class AtomTransmutationConfigurator(IConfigurator):
    """
    This configurator allow to select among the User Definitions, an atomic transmutation.
    Without any transmutation, all the atoms records into the trajectory keep there own types.
    If a transmutation is define, the analysis will consider atoms of a certain type 
    exactly like if they have another type, respectfully to the transmutation definition.
    
    To Build an atomic transmutation definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Atom transmutation" plugin
    """
    type = 'atom_transmutation'
                                
    def configure(self, configuration, value):

        self["value"] = value  
        
        if value is None:
            return

        self["atom_selection"] = configuration[self._dependencies['atom_selection']]
        if self["atom_selection"]["level"] != "atom":
            raise ConfiguratorError("the atom transmutation can only be set with a grouping level set to %r" % 'atom', self)

        trajConfig = configuration[self._dependencies['trajectory']]
                                                                
        parser = SelectionParser(trajConfig["universe"])
        
        # If the input value is a dictionary, it must have a selection string or a python script as key and the element 
        # to be transmutated to as value 
        if isinstance(value,dict):
            for expression,element in value.items():
                expression, selection = parser.select(expression, True)                    
                self.transmutate(configuration, selection, element)
          
        # Otherwise, it must be a list of strings that will be found as user-definition keys
        elif isinstance(value,(list,tuple)):                        
            for definition in value:
                
                ud = USER_DEFINITIONS.get(trajConfig["basename"],"atom_transmutation",definition)
                if ud is not None:
                    self.transmutate(configuration, ud["indexes"], ud["element"])
                else:
                    raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
                    or a list of string that match an user definition",self)
        else:
            raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
            or a list of string that match an user definition",self)

    def transmutate(self, configuration, selection, element):
        
        if element not in ELEMENTS:
            raise ConfiguratorError("the element %r is not registered in the database" % element, self)
                
        for idx in selection:
            try:
                pos = self["atom_selection"]["groups"].index([idx])
                
            except ValueError:
                continue
            
            else:
                self["atom_selection"]["elements"][pos] = [element]
                
        configuration.configurators[self._dependencies['atom_selection']].set_contents(configuration)

    def get_information(self):
        
        if self["value"] is None:
            return "No atoms selected for deuteration"
        
        return "Number of selected atoms for deuteration:%d\n" % self["atom_selection"]["n_selected_atoms"]