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

from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator

LEVELS = collections.OrderedDict()
LEVELS["atom"]     = {"atom" : 0, "atomcluster" : 0, "molecule" : 0, "nucleotidechain" : 0, "peptidechain" : 0, "protein" : 0}
LEVELS["group"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 1, "peptidechain" : 1, "protein" : 1}
LEVELS["residue"]  = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 2, "peptidechain" : 2, "protein" : 2}
LEVELS["chain"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 3}
LEVELS["molecule"] = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 4}
        
class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to choose the level of granularity in the atom selection.
    
    When reading the trajectory, the level of granularity will be applied by grouping the atoms of the selection
    to a single dummy-atoms located on the center of gravity of those atoms.
    
    The level of granularity currently supported are:
    
    * 'atom': no grouping will be performed
    * 'group': the atoms that belongs to a MMTK AtomCluster object will be grouped as a single atom per object while the ones that belongs to a MMTK Molecule, NucleotideChain, PeptideChain and Protein object will be grouped according to the chemical group they belong to (e.g. peptide group, methyl group ...)
    * 'residue': the atoms that belongs to a MMTK AtomCluster or Molecule object will be grouped as a single atom per object while the ones thta belongs to a MMTK NucleotideChain, PeptideChain or Protein object will be grouped according to the residue to which they belong to (e.g. Histidine, Cytosyl ...)
    * 'chain': the atoms that belongs to a MMTK AtomCluster or Molecule object will be grouped as a single atom per object while the ones that belongs to a MMTK NucleotideChain, PeptideChain or Protein object will be grouped according to the chain they belong to
    * 'molecule': the atoms that belongs to any MMTK chemical object will be grouped as a single atom per object
    """
    
    type = 'grouping_level'
    
    _default = "atom"
    
    def __init__(self, name, choices=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration
        :type name: str
        :param choices: the level of granularities allowed for the input value. If None all levels are allowed.
        :type choices: one of ['atom','group','residue','chain','molecule'] or None        
        '''
        
        if choices is None:
            choices = LEVELS.keys()
        else:
            choices = list(set(LEVELS.keys()).intersection(choices))

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)
    
    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Grouping level: %r\n" % self["value"]