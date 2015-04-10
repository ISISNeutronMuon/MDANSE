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

import collections
import operator

import numpy

from MDANSE.Framework.UserDefinables.UserDefinitions import USER_DEFINITIONS
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
    To Build an atom selection you have to :
    * Create a workspace based on a mmtk_trajectory data
    * drag a molecular viewer on it
    * drag into the Molecular Viewer his "Atom selection" plugin
    '''

    type = 'atom_selection'
    
    _default = "all"
                    
    def configure(self, configuration, value):
                          
        trajConfig = configuration[self._dependencies['trajectory']]
        
        if value is None:
            value = "all"
        
        if not isinstance(value,basestring):
            raise ConfiguratorError("invalid type for atom selection. Must be a string", self)
        
        self["value"] = value
        
        ud = USER_DEFINITIONS.get(trajConfig["basename"],"atom_selection",value)        
        if ud is not None:
            self.update(ud)
        else:
            parser = AtomSelectionParser(trajConfig["instance"])
            parser.parse(value)
            self.update(parser.definition)

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
        
        for _ in range(level):
            atom = atom.parent
            
        return atom
    
    def group(self, selectedAtoms, level="atom"):
                        
        level = level.strip().lower()
                
        groups = collections.OrderedDict()
        
        for i, idx in enumerate(self["indexes"]):
            at = selectedAtoms[i]
            lvl = LEVELS[level][at.topLevelChemicalObject().__class__.__name__.lower()]
            parent = self.find_parent(at,lvl)        
            groups.setdefault(parent,[]).append(idx)
        
        self["groups"] = groups.values()
            
        self["n_groups"] = len(self["groups"])
        
        if level != "atom":
            self["elements"] = [["dummy"]]*self["n_groups"]
                                        
        self["level"] = level
                
        self.set_contents()
                        
    def set_contents(self):
                
        self["contents"] = collections.OrderedDict()
        self['index_to_symbol'] = collections.OrderedDict()
        for i, group in enumerate(self["elements"]):
            for j, el in enumerate(group):
                self["contents"].setdefault(el,[]).append(self["groups"][i][j])
                self['index_to_symbol'][self["groups"][i][j]] = el
                 
        for k,v in self["contents"].items():
            self["contents"][k] = numpy.array(v)
            
        self["n_atoms_per_element"] = dict([(k,len(v)) for k,v in self["contents"].items()])              
        self['n_selected_elements'] = len(self["contents"])
                        
    def get_information(self):
        
        info = []
        info.append("Number of selected atoms:%d\n" % self["n_selected_atoms"])
        info.append("Level of selection:%s\n" % self["level"])
        info.append("Number of selected groups:%d\n" % self["n_groups"])
        info.append("Selected elements:%s\n" % self["contents"].keys())
        
        return "".join(info)