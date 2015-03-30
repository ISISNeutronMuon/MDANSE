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

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator

LEVELS = collections.OrderedDict()
LEVELS["atom"]     = {"atom" : 0, "atomcluster" : 0, "molecule" : 0, "nucleotidechain" : 0, "peptidechain" : 0, "protein" : 0}
LEVELS["group"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 1, "peptidechain" : 1, "protein" : 1}
LEVELS["residue"]  = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 2, "peptidechain" : 2, "protein" : 2}
LEVELS["chain"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 3}
LEVELS["molecule"] = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 4}
        
class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """
    This configurator allow to choose the level of coarseness which will be apply into the calculation
    """
    
    type = 'grouping_level'
    
    _default = "atom"
    
    def __init__(self, name, choices=None, **kwargs):
        
        choices = choices if choices is not None else LEVELS.keys()

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)
    
    def configure(self, configuration, value):
        
        value = value.lower()
        
        if not value in LEVELS.keys():
            raise ConfiguratorError("%r is not a valid grouping level." % value, self)

        self["value"] = value

    def get_information(self):
        
        return "Grouping level: %r\n" % self["value"]