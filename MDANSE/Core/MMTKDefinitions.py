import cPickle
import os

from MMTK.Biopolymers import defineAminoAcidResidue, defineNucleicAcidResidue
from MMTK.PDB import defineMolecule

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class MMTKDefinitionsError(Error):
    pass

class MMTKDefinitions(dict):

    __metaclass__ = Singleton
    
    _path = os.path.join(PLATFORM.application_directory(),"mmtk_definitions")
    
    _types = ['amino_acid','molecule','nucleic_acid']
                                                                                 
    def add(self, name, typ, databaseName):
        
        if type not in self._types:
            raise MMTKDefinitionsError('The type %r is not a valid MMTK definition type. It must be one of %s' % (str(name),MMTKDefinitions._types))
                        
        try:
            if typ == 'molecule':
                defineMolecule(name,databaseName)
            elif typ == 'amino_acid':
                defineAminoAcidResidue(databaseName,name)
            elif typ == 'nucleic_acid':
                defineNucleicAcidResidue(databaseName,name)
        except ValueError as e:
            raise MMTKDefinitions(str(e))
        else:
            self[name] = (typ,databaseName)
        
    def load(self):
        
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