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

from MDANSE import ELEMENTS
from MDANSE.Framework.UserDefinitionsStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParser
        
class AtomTransmutationConfigurator(IConfigurator):
    """
    This configurator allows to define a set of atoms to be transmutated to a given chemical
    element.
    
    For some analysis it can be necessary to change the nature of the chemical element of a given
    part of the system to have results closer to experience. A good example is to change some 
    hydrogen atoms to deuterium in order to fit with experiments where deuteration experiments have 
    been performed for improving the contrast and having a better access to the dynamic of a specific part
    of the molecular system.
            
    :note: this configurator depends on 'trajectory' and 'atom_selection' configurators to be configured
    """
    
    type = 'atom_transmutation'
    
    _default = None
                                
    def configure(self, configuration, value):
        '''
        Configure an input value. 
        
        The value can be:
        
        #. ``None``: no transmutation is performed
        #. (str,str)-dict: for each (str,str) pair, a transmutation will be performed by parsing \
        the 1st element as an atom selection string and transmutating the corresponding atom \
        selection to the target chemical element stored in the 2nd element
        #. str: the transmutation will be performed by reading the corresponding user definition
        
        :param configuration: the current configuration
        :type configuration: MDANSE.Framework.Configurable.Configurable
        :param value: the input value
        :type value: None or (str,str)-dict or str 
        '''

        self["value"] = value  
        
        # if the input value is None, do not perform any transmutation
        if value is None:
            return

        self["atom_selection"] = configuration[self._dependencies['atom_selection']]
        if self["atom_selection"]["level"] != "atom":
            raise ConfiguratorError("the atom transmutation can only be set with a grouping level set to %r" % 'atom', self)

        trajConfig = configuration[self._dependencies['trajectory']]
                                                                
        parser = AtomSelectionParser(trajConfig["instance"].universe)
        
        # If the input value is a dictionary, it must have a selection string as key and the element 
        # to be transmutated to as value 
        if isinstance(value,dict):
            for expression,element in value.items():
                indexes = parser.parse(element,expression)
                self.transmutate(configuration, indexes, element)
          
        # Otherwise, it must be a list of strings that will be found as user-definition keys
        elif isinstance(value,(list,tuple)):                        
            for definition in value:
                
                if UD_STORE.has_definition(trajConfig["basename"],"atom_transmutation",value):                
                    ud = UD_STORE.get_definition(trajConfig["basename"],"atom_transmutation",definition)
                    self.transmutate(configuration, ud["indexes"], ud["element"])
                else:
                    raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
                    or a list of string that match an user definition",self)
        else:
            raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
            or a list of string that match an user definition",self)

    def transmutate(self, configuration, selection, element):
        '''
        Transmutates a set of atoms to a given element 
        
        :param configuration: the current configuration
        :type configuration: MDANSE.Framework.Configurable.Configurable
        :param selection: the indexes of the atoms to be transmutated
        :type selection: list of int
        :param element: the symbol of the element to which the selected atoms should be transmutated
        :type element: str
        '''
        
        if element not in ELEMENTS:
            raise ConfiguratorError("the element %r is not registered in the database" % element, self)
                
        for idx in selection:
            pos = self["atom_selection"]["groups"].index([idx])
            self["atom_selection"]["elements"][pos] = [element]

        # Update the current configuration according to the changes triggered by
        # atom transumutation                
        configuration[self._dependencies['atom_selection']].set_contents()

    def get_information(self):
        '''
        Returns some informations the atoms selected for being transmutated.
        
        :return: the information about the atoms selected for being transmutated.
        :rtype: str
        '''

        if not self.has_key("value"):
            return "Not configured yet"
                
        if self["value"] is None:
            return "No atoms selected for deuteration"
        
        return "Number of selected atoms for deuteration:%d\n" % self["atom_selection"]["n_selected_atoms"]