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
from typing import Union, ItemsView

import json

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton


class _Database(metaclass=Singleton):
    """
    Base class for all the databases.
    """
    _DEFAULT_DATABASE: str
    _USER_DATABASE: str

    def __init__(self):
        """
        Constructor
        """

        self._data = {}

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load()

    def __contains__(self, name: str) -> bool:
        """
        Return True if the database contains the particle name.

        :param name: the name (default or alternative) of the nucleotide to search in the database
        :type name: str

        :return: True if the database contains a given element
        :rtype: bool
        """
        return name in self._residue_map

    def __iter__(self):
        """
        Return a generator over the particles stored in the database.
        """

        for v in self._data.values():
            yield copy.deepcopy(v)

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        if user_database is None:
            user_database = self._USER_DATABASE
        if default_database is None:
            default_database = self._DEFAULT_DATABASE

        if os.path.exists(user_database):
            database_path = user_database
        else:
            database_path = default_database

        with open(database_path, "r") as f:
            self._data = json.load(f)

    def _build_residue_map(self) -> None:
        """Creates a dict mapping alternative names to the official name."""
        self._residue_map = {}
        for k, v in self._data.items():
            self._residue_map[k] = k
            for alt in v['alternatives']:
                self._residue_map[alt] = k

    def items(self) -> ItemsView[str, dict]:
        """
        Returns the iterator over the items of the data dict, allowing for iteration over particle names and their data
        simultaneously.

        :return: an iterator over the items of the data dict
        :rtype: ItemsView
        """
        return self._data.items()

    def _reset(self) -> None:
        """
        Resets the database, removing all data.
        """
        self._data.clear()

    def save(self) -> None:
        """
        Save a copy of the database to MDANSE application directory. This database will then be used in the
        future. If the user database already exists, calling this function will overwrite it.
        """
        with open(self._USER_DATABASE, 'w') as f:
            json.dump(self._data, f)


class AtomsDatabaseError(Error):
    """
    This class handles the exceptions related to AtomsDatabase
    """
    pass


class AtomsDatabase(_Database):
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
        self._properties = {}

        super().__init__()

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

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the elements database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        super()._load(user_database, default_database)

        self._properties = self._data['properties']
        self._data = self._data['atoms']

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
        Add a new property to the atoms database.

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

    def get_values_for_multiple_atoms(self, atoms: list[str], prop: str) -> list[Union[str, int, float, list]]:
        """
        Retrieves the values of a given property for multiple atoms efficiently.
        :param atoms:
        :param prop:
        :return:
        """
        unique_atoms = set(atoms)

        if not all(atom in self._data for atom in atoms):
            raise AtomsDatabaseError('One or more of the provided atoms {} are unknown'.format(atoms))

        if prop not in self._properties:
            raise AtomsDatabaseError("The property {} is not registered in the database".format(prop))

        values = {name: self._data[name][prop] for name in unique_atoms}
        return [values[atom] for atom in atoms]

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


class MoleculesDatabase(_Database):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'molecules.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'molecules.json')

    def __getitem__(self, item: str):
        """
        Return an entry of the database.

        If the item is a basestring, then the return value will be the list of properties related to element of the
        database that matches this item. If the item is a 2-tuple then the return value will the property of the
        database whose element and property match respectively the first and second elements of the tuple.

        :param item: the item to get from the database
        :type item: str or tuple
        """

        if item in self._residue_map:
            return copy.deepcopy(self._data[self._residue_map[item]])
        else:
            raise MoleculesDatabaseError("The molecule {} is not registered in the database.".format(item))

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the molecule database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        super()._load(user_database, default_database)
        self._build_residue_map()

    def add_molecule(self, molecule: str) -> None:
        """
        Add a new molecule in the molecule database. The data for this molecule will be empty (not completely, its entry
        will consist of an empty list 'alternatives' and empty dict 'atoms') and will not be saved until the
        :meth: `save()` method is called. If the atom already exists, an exception is raised.

        :param molecule: the name of the molecule to add
        :type molecule: str
        """

        if molecule in self._data:
            raise MoleculesDatabaseError('The element {} is already stored in the database'.format(molecule))

        self._data[molecule] = {'alternatives': [], 'atoms': {}}
        self._residue_map[molecule] = molecule

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


class NucleotidesDatabaseError(Error):
    """
    This class handles the exceptions related to ElementsDatabase
    """
    pass


class NucleotidesDatabase(_Database):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'nucleotides.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'nucleotides.json')

    def __getitem__(self, item: str) -> dict[str, Union[bool, list[str], dict[str, Union[bool, list[str], str]]]]:
        """
        Return an entry of the database.

        If the item is a basestring, then the return value will be the list of properties related to element of the
        database that matches this item. If the item is a 2-tuple then the return value will the property of the
        database whose element and property match respectively the first and second elements of the tuple.

        :param item: the item to get from the database
        :type item: str or tuple
        """

        if item in self._residue_map:
            return copy.deepcopy(self._data[self._residue_map[item]])
        else:
            raise NucleotidesDatabaseError("The nucleotide {} is not registered in the database.".format(item))

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the molecule database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE nucleotide database. The default path is used by default.
        :type default_database: str or None
        """
        super()._load(user_database, default_database)
        self._build_residue_map()

    def add_nucleotide(self, nucleotide: str, is_5ter_terminus: bool = False, is_3ter_terminus: bool = False) -> None:
        """
        Add a new nucleotide in the nucleotide database. The data for this nucleotide will be empty (not completely,
        its entry will consist of an empty list 'alternatives' and empty dict 'atoms') and will not be saved until the
        :meth: `save()` method is called. If the atom already exists, an exception is raised.

        :param nucleotide: the name of the nucleotide to add
        :type nucleotide: str

        :param is_5ter_terminus: boolean value representing whether this nucleotide acts as a 5' terminus
        :type is_5ter_terminus: bool

        :param is_3ter_terminus: boolean value representing whether this nucleotide acts as a 3' terminus
        :type is_3ter_terminus: bool
        """

        if nucleotide in self._residue_map:
            raise NucleotidesDatabaseError('The nucleotide {} is already stored in the database'.format(nucleotide))

        self._data[nucleotide] = {
            'alternatives': [],
            'atoms': {},
            'is_5ter_terminus': is_5ter_terminus,
            'is_3ter_terminus': is_3ter_terminus}

        self._residue_map[nucleotide] = nucleotide

    @property
    def nucleotides(self) -> list[str]:
        """
        Returns the name of the nucleotides of the database.

        :return: the name of the nucleotides stored in the database
        :rtype: list
        """

        return list(self._data.keys())

    @property
    def n_nucleotides(self) -> int:
        """
        Return the number of nucleotides stored in the nucleotides database.

        :return: the number of nucleotides stored in the nucleotides database
        :rtype: int
        """

        return len(self._data)


class ResiduesDatabaseError(Error):
    """
    This class handles the exceptions related to ElementsDatabase
    """
    pass


class ResiduesDatabase(_Database):
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), 'residues.json')

    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), 'residues.json')

    def __getitem__(self, item: str) -> dict[str, Union[bool, list[str], dict[str, dict[str, Union[str, list[str]]]]]]:
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

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the molecule database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE nucleotide database. The default path is used by default.
        :type default_database: str or None
        """
        super()._load(user_database, default_database)
        self._build_residue_map()

    def add_residue(self, residue: str, is_c_terminus: bool = False, is_n_terminus: bool = False) -> None:
        """
        Add a new molecule to the residue database. The data for this residue will be empty (not completely, its entry
        will consist of an empty list 'alternatives', an empty dict 'atoms', and two booleans determined by the
        arguments) and will not be saved until the :meth: `save()` method is called. If the atom already exists, an
        exception is raised.

        :param residue: the name of the element to add
        :type residue: str

        :param is_c_terminus: boolean representation of whether this residue is the C-terminus of proteins. False by
               default.
        :type is_c_terminus: bool

        :param is_n_terminus: boolean representation of whether this residue is the N-terminus of proteins. False by
               default.
        :type is_n_terminus: bool
        """

        if residue in self._residue_map:
            raise ResiduesDatabaseError('The element {} is already stored in the database'.format(residue))

        self._data[residue] = {
            'alternatives': [],
            'atoms': {},
            'is_n_terminus': is_n_terminus,
            'is_c_terminus': is_c_terminus}

        self._residue_map[residue] = residue

    @property
    def residues(self) -> list[str]:
        """
        Returns the names of all residues in the database.

        :return: the names of all residues in the database.
        :rtype: list
        """

        return list(self._data.keys())

    @property
    def n_residues(self) -> int:
        """
        Return the number of residues stored in the residues database.

        :return: the number of residues stored in the residues database
        :rtype: int
        """

        return len(self._data)


if __name__ == '__main__':
    from MDANSE.Chemistry import ATOMS_DATABASE

    print(ATOMS_DATABASE.numeric_properties)
