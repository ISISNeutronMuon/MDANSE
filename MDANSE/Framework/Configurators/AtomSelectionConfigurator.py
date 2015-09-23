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

import numpy

from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
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
        
    :note: this configurator depends on 'trajectory' and 'grouping_level' configurators to be configured
    '''

    type = 'atom_selection'
    
    _default = "all"
                    
    def configure(self, configuration, value):
        '''
        Configure an input value. 
        
        The value must be a string that can be either an atom selection string or a valid user 
        definition.
        
        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input value
        :type value: str
        '''
                          
        trajConfig = configuration[self._dependencies['trajectory']]
        
        if value is None:
            value = ['all']
        
        if isinstance(value,basestring):
            value = [value]
        
        self["value"] = value
        
        self["indexes"] = []

        for v in value:
        
            if UD_STORE.has_definition(trajConfig["basename"],"atom_selection",v):
                ud = UD_STORE.get_definition(trajConfig["basename"],"atom_selection",v)
                self["indexes"].extend(ud["indexes"])
            else:        
                parser = AtomSelectionParser(trajConfig["instance"].universe)
                self["indexes"].extend(parser.parse(v))

        self["indexes"].sort()
        
        self["n_selected_atoms"] = len(self["indexes"])
        atoms = sorted(trajConfig["universe"].atomList(), key = operator.attrgetter('index'))
        selectedAtoms = [atoms[idx] for idx in self["indexes"]]
        self["elements"] = [[at.symbol] for at in selectedAtoms]

        if self._dependencies.has_key("grouping_level"):
            self.group(selectedAtoms, configuration[self._dependencies['grouping_level']]['value'])
        else:
            self.group(selectedAtoms)
                                 
        self.set_contents()
            
    @staticmethod                                                                                                                        
    def find_parent(atom, level):
        '''
        Retrieve recursively the parent of a given MMTK atom at a given level.
        For example, a level of 1 will return the direct parent of the atom. 
        
        :note: this is a static method
        
        :param atom: the atom for which the parent is searched for
        :type atom: MMTK.Atom object
        :param level: the level of the parent
        :type level: int
        '''
        
        for _ in range(level):
            atom = atom.parent
            
        return atom
    
    def group(self, atoms, level="atom"):
        '''
        Group the selected atoms according to a given granularity and update
        the configurator with the grouping results.
        
        :param atoms: the atoms for 
        :type atoms: list of MMTK.Atom
        :param level: the level of granularity at which the atoms should be grouped
        :type level: str
        '''
                                        
        groups = collections.OrderedDict()
        
        for at in atoms:
            lvl = LEVELS[level][at.topLevelChemicalObject().__class__.__name__.lower()]
            parent = self.find_parent(at,lvl)        
            groups.setdefault(parent,[]).append(at.index)
        
        self["groups"] = groups.values()
            
        self["n_groups"] = len(self["groups"])
        
        if level != "atom":
            self["elements"] = [["dummy"]]*self["n_groups"]
                                        
        self["level"] = level
                
        self.set_contents()
                        
    def set_contents(self):
        '''
        Sets the contents of the atom selection.
        '''
                    
        self["contents"] = collections.OrderedDict()
        self['index_to_symbol'] = collections.OrderedDict()
        for i, group in enumerate(self["elements"]):
            for j, el in enumerate(group):
                self["contents"].setdefault(el,[]).append(self["groups"][i][j])
                self['index_to_symbol'][self["groups"][i][j]] = el
                 
        for k,v in self["contents"].items():
            self["contents"][k] = numpy.array(v,dtype=numpy.int32)
            
        self["n_atoms_per_element"] = dict([(k,len(v)) for k,v in self["contents"].items()])              
        self['n_selected_elements'] = len(self["contents"])
                        
    def get_information(self):
        '''
        Returns some informations the atom selection.
        
        :return: the information about the atom selection.
        :rtype: str
        '''

        if not self.has_key("n_selected_atoms"):
            return "No configured yet"
        
        info = []
        info.append("Number of selected atoms:%d" % self["n_selected_atoms"])
        info.append("Level of selection:%s" % self["level"])
        info.append("Number of selected groups:%d" % self["n_groups"])
        info.append("Selected elements:%s" % self["contents"].keys())
        
        return "\n".join(info)