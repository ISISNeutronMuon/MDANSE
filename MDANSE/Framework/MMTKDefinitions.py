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

import cPickle
import os
import shutil

from MMTK.Biopolymers import defineAminoAcidResidue, defineNucleicAcidResidue
from MMTK.PDB import defineMolecule

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class MMTKDefinitionsError(Error):
    '''
    Handles the exceptions related to MMTKDefinitions.
    '''
    pass

class MMTKDefinitions(dict):
    '''
    This singleton class stores the patches for MMTK chemical database in a dictionary which is reloaded at MDANSE 
    start through the use of cPickle mechanism.
    
    When converting a trajectory, that uses PDB file format to define the system, to a MMTK trajectory, it may happen 
    that some molecules (molecule, amino acids, nucleic acids) are not defined in the default database shipped with MMTK. 
    In such case, it is compulsory to register them in order that they can be recognized as a valid molecule by MMTK.
    '''

    __metaclass__ = Singleton
    
    _path = os.path.join(PLATFORM.application_directory(),"mmtk_definitions")
    
    # These are the patchable types
    _types = ['amino_acid','molecule','nucleic_acid']
                                                                                 
    def add(self, code, typ, filename):
        '''
        Add a new MMTK definition to the MMTK definitions store.
        
        :param code: the MMTK code for the molecule to register (i.e. HOH for water)
        :type code: str
        :param typ: the molecular type for the molecule to register (one of 'amino_acid','molecule','nucleic_acid')
        :type typ: str
        :param filename: the filename that stores the MMTK definition of the molecule to register
        :type filename: str
        '''
        
        if typ not in self._types:
            raise MMTKDefinitionsError('The type %r is not a valid MMTK definition type. It must be one of %s' % (str(code),MMTKDefinitions._types))
                        
        # Extract the basename from the full name of the MMTK definition file
        basename = os.path.basename(filename)
        basename = os.path.splitext(basename)[0]
        
        # Define them in MMTK
        try:
            if typ == 'molecule':
                defineMolecule(code,basename)
                defPath = os.path.join(PLATFORM.local_mmtk_database_directory(),"Molecules")
            elif typ == 'amino_acid':
                defineAminoAcidResidue(basename,code)
                defPath = os.path.join(PLATFORM.local_mmtk_database_directory(),"Groups")
            elif typ == 'nucleic_acid':
                defineNucleicAcidResidue(basename,code)
                defPath = os.path.join(PLATFORM.local_mmtk_database_directory(),"Groups")
        except ValueError as e:
            raise MMTKDefinitionsError(str(e))
        else:
            defPath = os.path.join(defPath,basename)
            # Register the MMTK definition
            self[code] = (typ,basename)
            # Copy the MMTK definition file to the right place
            shutil.copy(filename,defPath)
            
    def load(self):
        '''
        Load the MMTK definitions file.
        '''
        
        if not os.path.exists(MMTKDefinitions._path):
            return

        # Try to open the UD file.
        try:
            with open(MMTKDefinitions._path, "rb") as f: 
                mmtkDef = cPickle.load(f)
                for name,(typ,databaseName) in mmtkDef.items():
                    self.add(name,typ,databaseName)
                    
        # If for whatever reason the pickle file loading failed do not even try to restore it
        except:
            raise MMTKDefinitionsError("The mmtk definitions file could not be loaded")
                    
    def save(self, path=None):
        '''
        Save the  MMTK definitions file
        
        :param path: the filename in which the MMTK definitions will be saved
        :type path: str
        '''
        
        if path is None:
            path = MMTKDefinitions._path
            
        try:                        
            f = open(path, "wb")
        except IOError:
            return
        else:
            cPickle.dump(self, f, protocol=2)
            f.close()

MMTK_DEFINITIONS = MMTKDefinitions()