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
from typing import Union, ItemsView

import json

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton


class AtomsDatabaseError(Error):
    """
    This class handles the exceptions related to AtomsDatabase
    """
    pass


class AtomsDatabase(metaclass=Singleton):
    """
    This class implements the atoms database of MDANSE.

    Storing all the chemical atoms (and their isotopes) is necessary for any analysis based
    on molecular dynamics trajectories. Indeed, most of them use atomic physico-chemical
    properties such as atomic weight, neutron scattering length, atomic radius ...

    The first time the user launches MDANSE, the database is initially loaded though a json file stored
    in a MDANSE default database path. Once modified, the user can save the database to a new csv file that
    will be stored in its MDANSE application directory (OS dependent). This is this file that will be loaded
    thereafter when starting MDANSE again.

    Once loaded, the database is stored internally in a nested dictionary whose primary keys are the name of the
    atoms and secondary keys the names of its associated properties.

    :Example:

    >>> # Import the database
    >>> from MDANSE.Chemistry import ATOMS_DATABASE
    >>>
    >>> # Fetch the hydrogen natural element --> get a deep-copy of its properties
    >>> hydrogen = ATOMS_DATABASE["H"]
    >>>
    >>> # Fetch the hydrogen H1 isotope --> get a deep-copy of its properties
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
    """

    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'atoms.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'atoms.json')

    # The python types supported by the database
    _TYPES = {"str": str, "int": int, "float": float, "list": list}

    def __init__(self):
        """
        Constructor
        """

        self._data = {}

        self._properties = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __contains__(self, element: str) -> bool:
        """
        Return True if the database contains a given element.

        :param ename: the name of the element to search in the database
        :type ename: str

        :return: True if the database contains a given element
        :rtype: bool
        """

        return element in self._data

    def __getitem__(self, item: str) -> dict:
        """
        Return an entry of the database. The return value is a deep copy of the element to preserve the database
        integrity.

        :param item: the item to get from the database
        :type item: str
        """

        try:
            return copy.deepcopy(self._data[item])
        except KeyError:
            raise AtomsDatabaseError("The element {} is not registered in the database.".format(item))

    def __iter__(self):
        """
        Return a generator over the atoms stored in the database.
        """

        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the elements database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        if user_database is None:
            user_database = AtomsDatabase._USER_DATABASE
        if default_database is None:
            default_database = AtomsDatabase._DEFAULT_DATABASE

        if os.path.exists(user_database):
            database_path = user_database
        else:
            database_path = default_database

        with open(database_path, "r") as f:
            db = json.load(f)
            self._properties = db['properties']
            self._data = db['atoms']

    def add_atom(self, atom: str) -> None:
        """
        Add a new element to the atoms database. The data for this atom will be empty and will not be saved until the
        :meth: `save()` method is called. If the atom already exists, an exception is raised.

        :param atom: the name of the element to add
        :type atom: str
        """

        if atom in self._data:
            raise AtomsDatabaseError('The atom {} is already stored in the database'.format(atom))

        self._data[atom] = {}

    def add_property(self, pname: str, ptype: str) -> None:
        """
        Add a new property to the elements database.

        When added, the property will be set with a default value to all the elements of the database.

        :param pname: the name of the property to add
        :type pname: str
        :param ptype: the type of the property
        :type ptype: one of "str","int", "float" or "list"
        """

        if pname in self._properties:
            raise AtomsDatabaseError("The property {} is already registered in the database.".format(pname))

        if ptype not in AtomsDatabase._TYPES:
            raise AtomsDatabaseError("The property type {} is unknown".format(ptype))

        self._properties[pname] = ptype
        ptype = AtomsDatabase._TYPES[ptype]

        for element in self._data.values():
            element[pname] = ptype()

    @property
    def atoms(self) -> list[str]:
        """
        Returns the names of all the atoms in the database, sorted alphabetically.

        :return: the name of the atoms stored in the database
        :rtype: list
        """

        return sorted(self._data.keys())

    def get_isotopes(self, atom: str) -> list[str]:
        """
        Get the name of the isotopes of a given atom.

        :param atom: the name of the atom whose isotopes are to be searched
        :type atom: str

        :return: the name of the isotopes corresponding to the selected atom
        :rtype: list
        """

        if atom not in self._data:
            raise AtomsDatabaseError('The atom {} is unknown'.format(atom))

        # The isotopes are searched according to |symbol| property
        symbol = self._data[atom]["symbol"]

        return [iname for iname, props in self._data.items() if props["symbol"] == symbol]

    @property
    def properties(self) -> list[str]:
        """
        Return the names of the properties stored in the atoms database.

        :return: the properties stored in the atoms database, sorted alphabetically
        :rtype: list
        """

        return sorted(self._properties.keys())

    def get_property(self, pname: str) -> dict[str, Union[str, int, float, list]]:
        """
        Returns a dictionary of the value of a given property for all the atoms of the database.

        :param pname: the name of the property to search in the database
        :type pname: str

        :return: a dictionary of the value of a given property for all the atoms of the database
        :rtype: dict
        """

        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        ptype = AtomsDatabase._TYPES[self._properties[pname]]

        return {element: properties.get(pname, ptype()) for element, properties in self._data.items()}

    def get_value(self, atom: str, pname: str) -> Union[str, int, float, list]:
        """
        Returns the value of a given property for a given atom. If the property is not set for this element
        returns the default value for the property type.

        :param atom: the name of the atom for which isotopes are searched
        :type atom: str
        :param pname: the name of the property to search in the database
        :type pname: str

        :return: the value
        :rtype: on of str, int, float, or list
        """

        if atom not in self._data:
            raise AtomsDatabaseError('The atom {} is unknown'.format(atom))

        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        ptype = self._properties[pname]
        ptype = AtomsDatabase._TYPES[ptype]

        return self._data[atom].get(pname, ptype())

    def set_value(self, atom: str, pname: str, value: Union[str, int, float, list]) -> None:
        """
        Set the given property of the given atom to the given value.

        :param atom: the name of the atom
        :type pname: str

        :param pname: the name of the property
        :type pname: str

        :param value: the value of the property
        :type value: one of str, int, float, or list
        """

        if atom not in self._data:
            raise AtomsDatabaseError('The element {} is unknown'.format(atom))

        if pname not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        try:
            self._data[atom][pname] = AtomsDatabase._TYPES[self._properties[pname]](value)
        except ValueError:
            raise AtomsDatabaseError("Can not coerce {} to {} type".format(value, self._properties[pname]))

    def has_atom(self, atom: str) -> bool:
        """
        Return True if the atoms database contains a given atom.

        :param atom: the name of the atom searched in the atoms database
        :type atom: str

        :return: True if the atoms database contains the selected atom
        :rtype: bool
        """

        return atom in self._data

    def has_property(self, pname: str) -> bool:
        """
        Return True if the atoms database contains a given property.

        :param pname: the name of the property searched in the atoms database
        :type pname: str

        :return: True if the atoms database contains the selected property
        :rtype: bool
        """

        return pname in self._properties

    def info(self, atom: str) -> str:
        """
        Return a formatted string that contains all the information about a given atom.

        :param atom: the name of the atom for which the property is required
        :type atom: str

        :return: the information about a selected atom
        :rype: str
        """

        # A delimiter line.
        delimiter = "-" * 70

        info = [delimiter, "%s" % atom.center(70), "%s" % " {0:<20}{1:>50}".format('property', 'value'), delimiter]

        # The values for all element's properties
        for pname in sorted(self._properties):
            info.append(" {0:<20}{1:>50}".format(pname, str(self._data[atom].get(pname, None))))

        info.append(delimiter)
        info = "\n".join(info)

        return info

    def items(self) -> ItemsView[str, Union[str, int, float, list]]:
        """
        Returns the iterator over the data dictionary, thus allowing to iterate over the atoms and their properties
        simultaneously.

        :return: Iterator over the data dictionary
        :rtype: ItemsView
        """
        return self._data.items()

    def match_numeric_property(self, pname: str, value: Union[int, float], tolerance:float = 0.0) -> list[str]:
        """
        Return the names of the atoms that match a given numeric property within a given tolerance

        :param pname: the name of the property to match
        :type pname: str
        :param value: the matching value
        :type value: one of int, float
        :param tolerance: the matching tolerance
        :type tolerance: float

        :return: the names of the atoms that matched the property with the selected value within the selected tolerance
        :rtype: list
        """
        try:
            if self._properties[pname] not in ['int', 'float']:
                raise AtomsDatabaseError(f'The provided property must be numeric, but "{pname}" has type '
                                         f"{self._properties[pname]}.")
        except KeyError:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(pname))

        tolerance = abs(tolerance)
        try:
            return [atom for atom, properties in self._data.items()
                    if abs(properties.get(pname, 0) - value) <= tolerance]
        except TypeError:
            raise AtomsDatabaseError(f'The provided value must be a numeric type, but {value} was provided, which is of'
                                     f' type {type(value)}. If you are sure that {value} is numeric, then your database'
                                     f' might be corrupt.')

    @property
    def n_atoms(self) -> int:
        """
        Return the number of atoms stored in the atoms database.

        :return: the number of atoms stored in the atoms database
        :rtype: int
        """

        return len(self._data)

    @property
    def n_properties(self) -> int:
        """
        Return the number of properties stored in the atoms database.

        :return: the number of properties stored in the atoms database
        :rtype: int
        """

        return len(self._properties)

    @property
    def numeric_properties(self) -> list[str]:
        """
        Return the names of the numeric properties stored in the atoms database.

        :return: the name of the numeric properties stored in the atoms database
        :rtype: list
        """
        return [pname for pname, prop in self._properties.items() if prop in ['int', 'float']]

    def _reset(self) -> None:
        """
        Reset the elements database
        """

        self._data.clear()

        self._properties.clear()

    def save(self) -> None:
        """
        Save a copy of the elements database to MDANSE application directory.
        """

        d = {'properties': self._properties, 'atoms': self._data}

        with open(AtomsDatabase._USER_DATABASE, 'w') as fout:
            json.dump(d, fout)


class MoleculesDatabaseError(Error):
    """
    This class handles the exceptions related to MoleculesDatabase
    """
    pass


class MoleculesDatabase(object, metaclass=Singleton):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'molecules.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'molecules.json')

    def __init__(self):
        """
        Constructor
        """

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __contains__(self, molecule: str) -> bool:
        """
        Return True if the database contains a given molecule.

        :param molecule: the name of the element to search in the database
        :type molecule: str

        :return: True if the database contains a given element
        :rtype: bool
        """

        for k, v in self._data.items():
            if molecule == k or molecule in v['alternatives']:
                return True

        return False

    def __getitem__(self, item: str):
        """
        Return an entry of the database.

        If the item is a basestring, then the return value will be the list of properties related to element of the
        database that matches this item. If the item is a 2-tuple then the return value will the property of the
        database whose element and property match respectively the first and second elements of the tuple.

        :param item: the item to get from the database
        :type item: str or tuple
        """

        for k, v in self._data.items():
            if item == k or item in v['alternatives']:
                return copy.deepcopy(self._data[k])
        else:
            raise MoleculesDatabaseError("The molecule {} is not registered in the database.".format(item))

    def __iter__(self):
        """
        Return a generator over the molecules stored in the database.
        """

        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the molecule database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        if user_database is None:
            user_database = MoleculesDatabase._USER_DATABASE
        if default_database is None:
            default_database = MoleculesDatabase._DEFAULT_DATABASE

        if os.path.exists(user_database):
            database_path = user_database
        else:
            database_path = default_database

        with open(database_path, "r") as f:
            self._data = json.load(f)

    def add_molecule(self, molecule: str) -> None:
        """
        Add a new molecule in the molecule database.The data for this atom will be empty (not completely, its entry
        will consist of an empty list 'alternatives' and empty dict 'atoms') and will not be saved until the
        :meth: `save()` method is called. If the atom already exists, an exception is raised.

        :param molecule: the name of the molecule to add
        :type molecule: str
        """

        if molecule in self._data:
            raise MoleculesDatabaseError('The element {} is already stored in the database'.format(molecule))

        self._data[molecule] = {'alternatives': [], 'atoms': {}}

    def items(self) -> ItemsView[str, dict[str, Union[list[str], dict[str, dict[str, Union[str, list[str]]]]]]]:
        """
        Returns an interator over the data dictionary, allowing to iterate over molecule names and their data
        simultaneously.

        :return: An iterator over the data dictionary
        :rtype: ItemsView
        """
        return self._data.items()

    @property
    def molecules(self) -> list[str]:
        """
        Returns the name of the molecule of the database.

        :return: the name of the molecule stored in the database
        :rtype: list
        """

        return list(self._data.keys())

    @property
    def n_molecules(self) -> int:
        """
        Return the number of molecules stored in the molecule database.

        :return: the number of molecules stored in the molecule database
        :rtype: int
        """

        return len(self._data)

    def _reset(self) -> None:
        """
        Reset the molecules database
        """

        self._data.clear()

    def save(self) -> None:
        """
        Save a copy of the molecule database to MDANSE application directory. This database will then be used in the
        future. If the user database already exists, calling this function will overwrite it.
        """

        with open(MoleculesDatabase._USER_DATABASE, 'w') as fout:
            json.dump(self._data, fout)


class NucleotidesDatabaseError(Error):
    """
    This class handles the exceptions related to ElementsDatabase
    """
    pass


class NucleotidesDatabase(object, metaclass=Singleton):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'nucleotides.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'nucleotides.json')

    def __init__(self):
        """
        Constructor
        """

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __contains__(self, nucleotide):
        """
        Return True if the database contains a given molecule.

        :param molecule: the name of the element to search in the database
        :type ename: str

        :return: True if the database contains a given element
        :rtype: bool
        """

        return nucleotide in self._residue_map

    def __getitem__(self, item):
        """
        Return an entry of the database.

        If the item is a basestring, then the return value will be the list of properties
        related to element of the databse base that matches this item. If the item is a
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.

        :param item: the item to get from the database
        :type item: str or tuple
        """

        if item in self._residue_map:
            return copy.deepcopy(self._data[self._residue_map[item]])
        else:
            raise NucleotidesDatabaseError("The nucleotide {} is not registered in the database.".format(item))

    def __iter__(self):
        """
        Return a generator over the nucleotides stored in the database.
        """

        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self):
        """
        Load the elements database

        :param filename: the path of the elements database to be loaded
        :type filename: str
        """

        if os.path.exists(NucleotidesDatabase._USER_DATABASE):
            database_path = NucleotidesDatabase._USER_DATABASE
        else:
            database_path = NucleotidesDatabase._DEFAULT_DATABASE

        f = open(database_path, 'r')

        # Try to open the input file
        try:
            self._data = json.load(f)
        except:
            raise NucleotidesDatabaseError('An error occured while parsing the molecules database')
        finally:
            f.close()

        self._residue_map = {}

        for k, v in self._data.items():
            self._residue_map[k] = k
            for alt in v['alternatives']:
                self._residue_map[alt] = k

    def add_nucleotide(self, nucleotide, is_5ter_terminus=False, is_3ter_terminus=False):
        """
        Add a new molecule in the elements database.

        :param ename: the name of the element to add
        :type ename: str
        """

        if nucleotide in self._data:
            raise NucleotidesDatabaseError('The nucleotide {} is already stored in the database'.format(nucleotide))

        self._data[nucleotide] = {
            'alternatives': [],
            'atoms': {},
            'is_5ter_terminus': is_5ter_terminus,
            'is_3ter_terminus': is_3ter_terminus}

    def items(self):

        return self._data.items()

    @property
    def nucleotides(self):
        """
        Returns the name of the nucleotides of the database.

        :return: the name of the elements stored in the database
        :rtype: list
        """

        return list(self._data.keys())

    @property
    def n_nucleotides(self):
        """
        Return the number of nucleotides stored in the elements database.

        :return: the number of elements stored in the elements database
        :rtype: int
        """

        return len(self._data)

    def _reset(self):
        """
        Reset the molecules database
        """

        self._data.clear()

    def save(self):
        """
        Save a copy of the elements database to MDANSE application directory.
        """

        with open(NucleotidesDatabase._USER_DATABASE, 'w') as fout:
            json.dump(self._data, fout)


class ResiduesDatabaseError(Error):
    """
    This class handles the exceptions related to ElementsDatabase
    """
    pass


class ResiduesDatabase(object, metaclass=Singleton):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'residues.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'residues.json')

    def __init__(self):
        """
        Constructor
        """

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __contains__(self, residue):
        """
        Return True if the database contains a given molecule.

        :param molecule: the name of the element to search in the database
        :type ename: str

        :return: True if the database contains a given element
        :rtype: bool
        """

        return residue in self._residue_map

    def __getitem__(self, item):
        """
        Return an entry of the database.

        If the item is a basestring, then the return value will be the list of properties
        related to element of the databse base that matches this item. If the item is a
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.

        :param item: the item to get from the database
        :type item: str or tuple
        """

        if item in self._residue_map:
            return copy.deepcopy(self._data[self._residue_map[item]])
        else:
            raise ResiduesDatabaseError("The residue {} is not registered in the database.".format(item))

    def __iter__(self):
        """
        Return a generator over the molecules stored in the database.
        """

        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self):
        """
        Load the elements database

        :param filename: the path of the elements database to be loaded
        :type filename: str
        """

        if os.path.exists(ResiduesDatabase._USER_DATABASE):
            database_path = ResiduesDatabase._USER_DATABASE
        else:
            database_path = ResiduesDatabase._DEFAULT_DATABASE

        f = open(database_path, 'r')

        # Try to open the input file
        try:
            self._data = json.load(f)
        except:
            raise ResiduesDatabaseError('An error occured while parsing the molecules database')
        finally:
            f.close()

        self._residue_map = {}

        for k, v in self._data.items():
            self._residue_map[k] = k
            for alt in v['alternatives']:
                self._residue_map[alt] = k

    def add_residue(self, residue, is_c_terminus=False, is_n_terminus=False):
        """
        Add a new molecule in the elements database.

        :param ename: the name of the element to add
        :type ename: str
        """

        if residue in self._data:
            raise ResiduesDatabaseError('The element {} is already stored in the database'.format(residue))

        self._data[residue] = {
            'alternatives': [],
            'atoms': {},
            'is_n_terminus': is_n_terminus,
            'is_c_terminus': is_c_terminus}

    def items(self):

        return self._data.items()

    @property
    def residues(self):
        """
        Returns the name of the elements of the database.

        :return: the name of the elements stored in the database
        :rtype: list
        """

        return list(self._data.keys())

    @property
    def n_residues(self):
        """
        Return the number of elements stored in the elements database.

        :return: the number of elements stored in the elements database
        :rtype: int
        """

        return len(self._data)

    def _reset(self):
        """
        Reset the molecules database
        """

        self._data.clear()

    def save(self):
        """
        Save a copy of the elements database to MDANSE application directory.
        """

        with open(ResiduesDatabase._USER_DATABASE, 'w') as fout:
            json.dump(self._data, fout)


if __name__ == '__main__':
    from MDANSE.Chemistry import ATOMS_DATABASE

    print(ATOMS_DATABASE.numeric_properties)
