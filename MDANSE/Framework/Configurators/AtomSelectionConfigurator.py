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

import collections
import operator


from MDANSE import ELEMENTS
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParser

# The granularities at which the selection will be performed
LEVELS = collections.OrderedDict()
LEVELS["atom"]     = {"atom" : 0, "atomcluster" : 0, "molecule" : 0, "nucleotidechain" : 0, "peptidechain" : 0, "protein" : 0}
LEVELS["group"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 1, "peptidechain" : 1, "protein" : 1}
LEVELS["residue"]  = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 2, "peptidechain" : 2, "protein" : 2}
LEVELS["chain"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 3}
LEVELS["molecule"] = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 4}

class AtomSelectionConfigurator(IConfigurator):    
    '''
    This configurator allows the selection of a specific set of atoms on which the analysis will be performed.

    Without any selection, all the atoms stored into the trajectory file will be selected.
    
    After the call to :py:meth:`~MDANSE.Framework.Configurators.AtomSelectionConfigurator.AtomSelectionConfigurator.configure` method 
    the following keys will be available for this configurator
    
    #. value: the input value used to configure this configurator
    #. indexes: the sorted (in increasing order) MMTK indexes of the selected atoms 
    #. n_selected_atoms: the number of selected atoms
    #. elements: a nested-list of the chemical symbols of the selected atoms. The size of the nested list depends on the 
    grouping_level selected via :py:class:`~MDANSE.Framework.Configurators.GroupingLevelConfigurator.GroupingLevelConfigurator`
    configurator.
    
        
    :note: this configurator depends on :py:class:`~MDANSE.Framework.Configurators.MMTKTrajectoryConfigurator.MMTKTrajectoryConfigurator` 
    and :py:class:`~MDANSE.Framework.Configurators.GroupingLevelConfigurator.GroupingLevelConfigurator` configurators to be configured
    '''

    type = 'atom_selection'
    
    _default = "all"
                    
    def configure(self, value):
        '''
        Configure an input value. 
        
        The value must be a string that can be either an atom selection string or a valid user 
        definition.
        
        :param value: the input value
        :type value: str
        '''
                          
        trajConfig = self._configurable[self._dependencies['trajectory']]
        
        if value is None:
            value = ['all']
        
        if isinstance(value,basestring):
            value = [value]

        if not isinstance(value,(list,tuple)):
            raise ConfiguratorError("Invalid input value.")
        
        self["value"] = value
        
        indexes = set()

        for v in value:
        
            if UD_STORE.has_definition(trajConfig["basename"],"atom_selection",v):
                ud = UD_STORE.get_definition(trajConfig["basename"],"atom_selection",v)
                indexes.update(ud["indexes"])
            else:        
                parser = AtomSelectionParser(trajConfig["instance"])
                indexes.update(parser.parse(v))

        indexes = sorted(list(indexes))

        atoms = sorted(trajConfig["universe"].atomList(), key = operator.attrgetter('index'))
        selectedAtoms = [atoms[idx] for idx in indexes]

        self["selection_length"] = len(indexes)        
        self['elements'] = [[at.symbol] for at in selectedAtoms]
        self['indexes'] = [[idx] for idx in indexes]
        self['names'] = [at.symbol for at in selectedAtoms]
        self['unique_names'] = sorted(set(self['names']))
        self['masses'] = [[ELEMENTS[n,'atomic_weight']] for n in self['names']]
                
    def get_natoms(self):
                
        nAtomsPerElement = {}
        for v in self["names"]:
            if nAtomsPerElement.has_key(v):
                nAtomsPerElement[v] += 1
            else:
                nAtomsPerElement[v] = 1
                
        return nAtomsPerElement
    
    def get_indexes(self):

        indexesPerElement = {}
        for i,v in enumerate(self["names"]):
            if indexesPerElement.has_key(v):
                indexesPerElement[v].extend(self['indexes'][i])
            else:
                indexesPerElement[v] = self['indexes'][i]
                
        return indexesPerElement
            
    def get_information(self):
        '''
        Returns some informations the atom selection.
        
        :return: the information about the atom selection.
        :rtype: str
        '''

        if not self.has_key("selection_length"):
            return "Not configured yet\n"
        
        info = []
        info.append("Number of selected atoms:%d" % self["selection_length"])
        info.append("Selected elements:%s" % self["unique_names"])
        
        return "\n".join(info)