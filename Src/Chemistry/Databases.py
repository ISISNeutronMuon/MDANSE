# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Data/ElementsDatabase.py
# @brief     Implements module/class/test ElementsDatabase
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import copy
import os
import numbers

import yaml

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class AtomsDatabaseError(Error):
    '''
    This class handles the exceptions related to AtomsDatabase
    '''
    pass

class AtomsDatabase:
    '''
    This class implements the atoms database of MDANSE.
    
    Storing all the chemical atoms (and their isotopes) is necessary for any analysis based 
    on molecular dynamics trajectories. Indeed, most of them use atomic physico-chemical 
    properties such as atomic weight, neutron scattering length, atomic radius ...
    
    The first time the user launches MDANSE, the database is initially loaded though a yaml file stored 
    in a MDANSE default database path. Once modified, the user can save the database to a new csv file that
    will be stored in its MDANSE application directory (OS dependent). This is this file that will be loaded 
    thereafter when starting MDANSE again. 
    
    Once loaded, the database is stored internally in a nested dictionary whose primary keys are the name of the 
    atoms and secondary keys the names of its associated properties.
        
    :Example:
    
    >>> # Import the database
    >>> from MDANSE.Chemistry import ATOMS_DATABASE
    >>> 
    >>> # Fetch the hydrogen natural element --> get a deep-copy of the its properties
    >>> hydrogen = ATOMS_DATABASE["H"]
    >>> 
    >>> # Fetch the hydrogen H1 isotope --> get a deep-copy of the its properties
    >>> h1 = ATOMS_DATABASE["H1"]
    >>> 
    >>> # Return a set of the properties stored in the database
    >>> l = ATOMS_DATABASE.properties()
    >>> 
    >>> # Return the atomic weight of U235 atom
    >>> w = ATOMS_DATABASE["U235"]["atomic_weight"]
    >>> 
    >>> # Returns the atoms stored currently in the database
    >>> atoms = ATOMS_DATABASE.atoms()
    '''
    
    __metaclass__ = Singleton
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__),"atoms.yml")
    
    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "atoms.yml")
    
    # The python types supported by the database
    _TYPES = {"str" : str, "int" : int, "float" : float, "list" : list}

    def __init__(self):
        '''
        Constructor
        '''

        self._data = {}

        self._properties = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()
                
    def __contains__(self,element):
        '''
        Return True if the database contains a given element.
        
        :param ename: the name of the element to search in the database
        :type ename: str
        
        :return: True if the database contains a given element
        :rtype: bool
        '''
        
        return self._data.has_key(element)

    def __getitem__(self,item):
        '''
        Return an entry of the database. The return value is a deep copy of the element to preserve the database integrity.
                
        :param item: the item to get from the database
        :type item: str
        '''

        try:
            return copy.deepcopy(self._data[item])
        except KeyError:                
            raise AtomsDatabaseError("The element {} is not registered in the database.".format(item))

    def __iter__(self):
        '''
        Return a generator over the atoms stored in the database.
        '''
                        
        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self):
        '''
        Load the elements database
        
        :param filename: the path of the elements database to be loaded
        :type filename: str
        '''

        if os.path.exists(AtomsDatabase._USER_DATABASE):
            databasePath = AtomsDatabase._USER_DATABASE
        else:
            databasePath = AtomsDatabase._DEFAULT_DATABASE

        with open(databasePath, "r") as f:
            db = yaml.safe_load(f)
            self._properties = db['properties']
            self._data = db['atoms']
        
    def add_atom(self, atom):
        '''
        Add a new element in the atoms database.
        
        :param ename: the name of the element to add
        :type ename: str
        '''
                    
        if self._data.has_key(atom):
            raise AtomsDatabaseError('The atom {} is already stored in the database'.format(atom))

        self._data[atom] = {}
            
    def add_property(self, pname, ptype):
        '''
        Add a new property to the elements database.
        
        When added, the property will be set with a default value to all the elements of the database.
        
        :param pname: the name of the property to add
        :type pname: str
        :param ptype: the type of the property
        :type ptype: one of "str","int", "float" or "list"
        '''
        
        if pname in self._properties:
            raise AtomsDatabaseError("The property {} is already registered in the database.".format(pname))

        if ptype not in AtomsDatabase._TYPES:
            raise AtomsDatabaseError("The property type {} is unknown".format(ptype))

        self._properties[pname] = ptype
        ptype = AtomsDatabase._TYPES[ptype]

        for element in self._data.values():
            element[pname] = ptype()
                                    
    @property
    def atoms(self):
        '''
        Returns the name of the atoms of the database.
        
        :return: the name of the atoms stored in the database
        :rtype: list
        '''
        
        return sorted(self._data.keys())

    def get_isotopes(self,atom):
        '''
        Get the name of the isotopes of a given atom.
        
        :param atom: the name of the atom for which isotopes are searched
        :type atom: str

        :return: the name of the isotopes corresponding to the selected atom
        :rtype: list
        '''
        
        if atom not in self._data:
            return AtomsDatabaseError('The atom {} is unknown'.format(atom))

        # The isotopes are searched according to |symbol| property
        symbol = self._data[atom]["symbol"]

        return [iname for iname,props in self._data.iteritems() if props["symbol"] == symbol]

    @property
    def properties(self):
        '''
        Return the names of the properties stored in the atoms database.

        :return: the properties stored in the atoms database
        :rtype: list
        '''

        return sorted(self._properties.keys())
        
    def get_property(self,pname):
        '''
        Returns a dictionary of the value of a given property for all the atoms of the database.
        
        :param pname: the name of the property to search in the database
        :type pname: str
        
        :return: a dictionary of the value of a given property for all the atoms of the database
        :rtype: dict
        '''
                
        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))
        
        ptype = AtomsDatabase._TYPES[self._properties[pname]]

        return dict([(element,properties.get(pname,ptype())) for element, properties in self._data.items()])

    def get_value(self, atom, pname):
        """Return the value of a given property for a given atom. If the property is not set for this element 
        returns the default value for the property type.

        :param atom: the name of the atom for which isotopes are searched
        :type atom: str
        :param pname: the name of the property to search in the database
        :type pname: str

        :return: the value
        :rtype: any
        """

        if atom not in self._data:
            return AtomsDatabaseError('The atom {} is unknown'.format(atom))

        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        ptype = self._properties[pname]
        ptype = AtomsDatabase._TYPES[ptype]

        return self._data[atom].get(pname,ptype())

    def set_value(self, atom, pname, value):
        """Set the property of a given atom.

        :param atom: the name of the atom
        :type pname: str
        :param pname: the name of the property
        :type pname: str
        :param value: the valur of the property
        :type value: any
        """
        
        if atom not in self._data:
            raise AtomsDatabaseError('The element {} is unknown'.format(atom))

        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        try:
            self._data[atom][pname] = AtomsDatabase._TYPES[self._properties[pname]](value)
        except:
            raise AtomsDatabaseError("Can not coerce {} to {} type".format(value,self._properties[pname]))

    def has_atom(self,atom):
        '''
        Return True if the atoms database contains a given atom.
        
        :param ename: the name of the atom searched in the atoms database
        :type ename: str
        
        :return: True if the atoms database contains the selected atom
        :rtype: bool
        '''
        
        return self._data.has_key(atom)

    def has_property(self,pname):
        '''
        Return True if the atoms database contains a given property.
        
        :param pname: the name of the property searched in the atoms database
        :type pname: str

        :return: True if the atoms database contains the selected property
        :rtype: bool
        '''
        
        return pname in self._properties

    def info(self, atom):
        '''
        Return a formatted string that contains all the informations about a given atom.
        
        :param atom: the name of the atom for which the property is required
        :type atom: str
        
        :return: the information about a selected atom
        :rype: str
        '''
                
        # A delimiter line.
        delimiter = "-"*70

        # The list that will contain the informations.
        info = []

        # Append a delimiter.                
        info.append(delimiter)

        # The name of the entry is centered in a centered-string.
        info.append("%s" % atom.center(70))
                        
        # The 'property' and 'value' columns names.
        info.append("%s" % " {0:<20}{1:>50}".format('property', 'value'))
                                
        # Append a delimiter.                
        info.append(delimiter)
                        
        # The values for all element's properties
        for pname in sorted(self._properties):
            info.append("%s" % " {0:<20}{1:>50}".format(pname,self._data[atom].get(pname,None)))

        # Append a delimiter.                
        info.append(delimiter)
                
        # The list is joined to a string.
        info = "\n".join(info)
                            
        # And returned.        
        return info

    def items(self):

        return self._data.items()

    def match_numeric_property(self, pname, value, tolerance=0.0):
        '''
        Return the names of the atoms that match a given numeric property within a given tolerance
        
        :param pname: the name of the property to to match
        :type pname: str
        :param value: the matching value
        :type value: one of int, float
        :param tolerance: the matching tolerance
        :type tolerance: float
        
        :return: the names of the atoms that matched the property with the selected value within the selected tolerance
        :rtype: list
        '''
        
        tolerance = abs(tolerance)

        pvalues = self.get_property(pname)

        return [ename for ename,pval in pvalues.items() if abs(pval-value)<tolerance]
           
    @property
    def n_atoms(self):
        '''
        Return the number of atoms stored in the atoms database.
        
        :return: the number of atoms stored in the atoms database
        :rtype: int
        '''

        return len(self._data)

    @property
    def n_properties(self):
        '''
        Return the number of properties stored in the atoms database.
        
        :return: the number of properties stored in the atoms database
        :rtype: int
        '''
        
        return len(self._properties)
    
    @property
    def numeric_properties(self):
        '''
        Return the names of the numeric properties stored in the atoms database.

        :return: the name of the numeric properties stored in the atoms database
        :rtype: list
        '''

        num_properties = []
        for pname, prop in self._properties.items():
            if not isinstance(prop,numbers.Number):
                num_properties.append(pname)
            
        return num_properties
            
    def _reset(self):
        '''
        Reset the elements database
        '''
        
        self._data.clear()

        self._properties.clear()
        
    def save(self):
        '''
        Save a copy of the elements database to MDANSE application directory. 
        '''
        
        d = {'properties':self._properties,'atoms':self._data}

        with open(AtomsDatabase._USER_DATABASE,'w') as fout:
            yaml.dump(d,fout)

    @property
    def n_atoms(self):
        return len(self._data)
            
class MoleculesDatabaseError(Error):
    '''
    This class handles the exceptions related to ElementsDatabase
    '''
    pass

class MoleculesDatabase(object):
    
    __metaclass__ = Singleton
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__),"molecules.yml")
    
    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "molecules.yml")
    
    def __init__(self):
        '''
        Constructor
        '''

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()
                
    def __contains__(self,molecule):
        '''
        Return True if the database contains a given molecule.
        
        :param molecule: the name of the element to search in the database
        :type ename: str
        
        :return: True if the database contains a given element
        :rtype: bool
        '''
        
        for k, v in self._data.items():
            if molecule == k or molecule in v['alternatives']:
                return True

        return False

    def __getitem__(self,item):
        '''
        Return an entry of the database.
        
        If the item is a basestring, then the return value will be the list of properties 
        related to element of the databse base that matches this item. If the item is a 
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.
        
        :param item: the item to get from the database
        :type item: str or tuple
        '''

        for k, v in self._data.items():
            if item == k or item in v['alternatives']:
                return copy.deepcopy(self._data[k])
        else:
            raise MoleculesDatabaseError("The molecule {} is not registered in the database.".format(item))

    def __iter__(self):
        '''
        Return a generator over the molecules stored in the database.
        '''
                        
        for v in self._data.values():
            yield copy.deepcopy(v)
            
    def _load(self):
        '''
        Load the elements database
        
        :param filename: the path of the elements database to be loaded
        :type filename: str
        '''

        if os.path.exists(MoleculesDatabase._USER_DATABASE):
            databasePath = MoleculesDatabase._USER_DATABASE
        else:
            databasePath = MoleculesDatabase._DEFAULT_DATABASE

        f = open(databasePath, "r")

        # Try to open the input file
        try:
            self._data = yaml.safe_load(f)
        except:
            raise MoleculesDatabaseError('An error occured while parsing the molecules database')
        finally:
            f.close()
        
    def add_molecule(self, molecule):
        '''
        Add a new molecule in the elements database.
        
        :param ename: the name of the element to add
        :type ename: str
        '''
                    
        if self._data.has_key(molecule):
            raise MoleculesDatabaseError('The element {} is already stored in the database'.format(molecule))

        self._data[molecule] = {'alternatives':[],'atoms':{}}

    def items(self):

        return self._data.items()

    @property
    def molecules(self):
        '''
        Returns the name of the elements of the database.
        
        :return: the name of the elements stored in the database
        :rtype: list
        '''
        
        return self._data.keys()
           
    @property
    def n_molecules(self):
        '''
        Return the number of elements stored in the elements database.
        
        :return: the number of elements stored in the elements database
        :rtype: int
        '''

        return len(self._data)

    def _reset(self):
        '''
        Reset the molecules database
        '''
        
        self._data.clear()
        
    def save(self):
        '''
        Save a copy of the elements database to MDANSE application directory. 
        '''
        
        with open(MoleculesDatabaseError._USER_DATABASE,'w') as fout:
            yaml.dump(self._data,fout)

class NucleotidesDatabaseError(Error):
    '''
    This class handles the exceptions related to ElementsDatabase
    '''
    pass

class NucleotidesDatabase(object):
    
    __metaclass__ = Singleton
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__),'nucleotides.yml')
    
    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'nucleotides.yml')
    
    def __init__(self):
        '''
        Constructor
        '''

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()
                
    def __contains__(self,nucleotide):
        '''
        Return True if the database contains a given molecule.
        
        :param molecule: the name of the element to search in the database
        :type ename: str
        
        :return: True if the database contains a given element
        :rtype: bool
        '''

        for k, v in self._data.items():
            if nucleotide == k or nucleotide in v['alternatives']:
                return True
        
        return False

    def __getitem__(self,item):
        '''
        Return an entry of the database.
        
        If the item is a basestring, then the return value will be the list of properties 
        related to element of the databse base that matches this item. If the item is a 
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.
        
        :param item: the item to get from the database
        :type item: str or tuple
        '''

        for k, v in self._data.items():
            if item == k or item in v['alternatives']:
                return copy.deepcopy(self._data[k])
        else:
            raise NucleotidesDatabaseError("The nucleotide {} is not registered in the database.".format(item))

    def __iter__(self):
        '''
        Return a generator over the nucleotides stored in the database.
        '''
                        
        for v in self._data.values():
            yield copy.deepcopy(v)
            
    def _load(self):
        '''
        Load the elements database
        
        :param filename: the path of the elements database to be loaded
        :type filename: str
        '''

        if os.path.exists(NucleotidesDatabase._USER_DATABASE):
            databasePath = NucleotidesDatabase._USER_DATABASE
        else:
            databasePath = NucleotidesDatabase._DEFAULT_DATABASE

        f = open(databasePath, 'r')

        # Try to open the input file
        try:
            self._data = yaml.safe_load(f)
        except:
            raise NucleotidesDatabaseError('An error occured while parsing the molecules database')
        finally:
            f.close()
        
    def add_nucleotide(self, nucleotide, is_5ter_terminus=False, is_3ter_terminus=False):
        '''
        Add a new molecule in the elements database.
        
        :param ename: the name of the element to add
        :type ename: str
        '''
                    
        if self._data.has_key(nucleotide):
            raise NucleotidesDatabaseError('The nucleotide {} is already stored in the database'.format(nucleotide))

        self._data[nucleotide] = {
            'alternatives' : [],
            'atoms' : {},
            'is_5ter_terminus' : is_5ter_terminus, 
            'is_3ter_terminus' : is_3ter_terminus}

    def items(self):

        return self._data.items()

    @property
    def nucleotides(self):
        '''
        Returns the name of the nucleotides of the database.
        
        :return: the name of the elements stored in the database
        :rtype: list
        '''
        
        return self._data.keys()
           
    @property
    def n_nucleotides(self):
        '''
        Return the number of nucleotides stored in the elements database.
        
        :return: the number of elements stored in the elements database
        :rtype: int
        '''

        return len(self._data)

    def _reset(self):
        '''
        Reset the molecules database
        '''
        
        self._data.clear()
        
    def save(self):
        '''
        Save a copy of the elements database to MDANSE application directory. 
        '''
        
        with open(NucleotidesDatabaseError._USER_DATABASE,'w') as fout:
            yaml.dump(self._data,fout)

class ResiduesDatabaseError(Error):
    '''
    This class handles the exceptions related to ElementsDatabase
    '''
    pass

class ResiduesDatabase(object):
    
    __metaclass__ = Singleton
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__),'residues.yml')
    
    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'residues.yml')
    
    def __init__(self):
        '''
        Constructor
        '''

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()
                
    def __contains__(self,residue):
        '''
        Return True if the database contains a given molecule.
        
        :param molecule: the name of the element to search in the database
        :type ename: str
        
        :return: True if the database contains a given element
        :rtype: bool
        '''
        
        return self._data.has_key(residue)

    def __getitem__(self,item):
        '''
        Return an entry of the database.
        
        If the item is a basestring, then the return value will be the list of properties 
        related to element of the databse base that matches this item. If the item is a 
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.
        
        :param item: the item to get from the database
        :type item: str or tuple
        '''

        try:
            return copy.deepcopy(self._data[item])
        except KeyError:                
            raise ResiduesDatabaseError("The residue {} is not registered in the database.".format(item))

    def __iter__(self):
        '''
        Return a generator over the molecules stored in the database.
        '''
                        
        for v in self._data.values():
            yield copy.deepcopy(v)
            
    def _load(self):
        '''
        Load the elements database
        
        :param filename: the path of the elements database to be loaded
        :type filename: str
        '''

        if os.path.exists(ResiduesDatabase._USER_DATABASE):
            databasePath = ResiduesDatabase._USER_DATABASE
        else:
            databasePath = ResiduesDatabase._DEFAULT_DATABASE

        f = open(databasePath, 'r')

        # Try to open the input file
        try:
            self._data = yaml.safe_load(f)
        except:
            raise ResiduesDatabaseError('An error occured while parsing the molecules database')
        finally:
            f.close()
        
    def add_residue(self, residue, is_c_terminus=False, is_n_terminus=False):
        '''
        Add a new molecule in the elements database.
        
        :param ename: the name of the element to add
        :type ename: str
        '''
                    
        if self._data.has_key(residue):
            raise ResiduesDatabaseError('The element {} is already stored in the database'.format(residue))

        self._data[residue] = {
            'alternatives' : [],
            'atoms' : {},
            'is_n_terminus' : is_n_terminus, 
            'is_c_terminus' : is_c_terminus}

    def items(self):

        return self._data.items()

    @property
    def residues(self):
        '''
        Returns the name of the elements of the database.
        
        :return: the name of the elements stored in the database
        :rtype: list
        '''
        
        return self._data.keys()
           
    @property
    def n_residues(self):
        '''
        Return the number of elements stored in the elements database.
        
        :return: the number of elements stored in the elements database
        :rtype: int
        '''

        return len(self._data)

    def _reset(self):
        '''
        Reset the molecules database
        '''
        
        self._data.clear()
        
    def save(self):
        '''
        Save a copy of the elements database to MDANSE application directory. 
        '''
        
        with open(ResiduesDatabaseError._USER_DATABASE,'w') as fout:
            yaml.dump(self._data,fout)

if __name__ == '__main__':

    from MDANSE.Chemistry import ATOMS_DATABASE

    print(ATOMS_DATABASE.numeric_properties)
