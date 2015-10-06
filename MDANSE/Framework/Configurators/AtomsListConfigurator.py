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

from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule

class AtomsListConfigurator(IConfigurator):    
    '''
    This configurator allows of a given list of atom names.

    The atoms has to belong to the same molecule.
        
    :note: this configurator depends on 'trajectory'
    '''

    type = 'atoms_list'
    
    _default = None
                    
    def __init__(self, configurable, name, nAtoms=2, **kwargs):
        '''
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param nAtoms: the (exact) number of atoms of the list.
        :type nAtoms: int
        '''
        
        IConfigurator.__init__(self, configurable, name, **kwargs)
        
        self._nAtoms = nAtoms
        
    @property
    def nAtoms(self):
        
        return self._nAtoms
    
    def configure(self, value):
        '''
        Configure an input value. 
        
        The value must be a string that can be either an atom selection string or a valid user 
        definition.
        
        :param value: the input value
        :type value: str
        '''
                          
        trajConfig = self._configurable[self._dependencies['trajectory']]
                
        if UD_STORE.has_definition(trajConfig["basename"],"%d_atoms_list" % self._nAtoms,value): 
            molecule,atoms = UD_STORE.get_definition(trajConfig["basename"],"%d_atoms_list" % self._nAtoms,value)
        else:
            molecule,atoms=value

        self["value"] = value
        
        self['atoms'] = find_atoms_in_molecule(trajConfig['instance'].universe,molecule, atoms, True)
                        
        self['n_values'] = len(self['atoms'])
                                    
    def get_information(self):
        '''
        Returns some informations the atom selection.
        
        :return: the information about the atom selection.
        :rtype: str
        '''

        if not self.has_key("atoms"):
            return "No configured yet"
        
        info = []
        info.append("Number of selected %d-tuplets:%d" % (self._nAtoms,self["n_values"]))
        
        return "\n".join(info)