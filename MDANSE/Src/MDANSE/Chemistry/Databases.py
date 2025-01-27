#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import copy
from typing import Union, ItemsView, Dict, Any
from pathlib import Path

import json

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton


class _Database(metaclass=Singleton):
    """
    Base class for all the databases.
    """

    _DEFAULT_DATABASE: Path
    _USER_DATABASE: Path

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

    def _load(
        self,
        user_database: Union[Path, str, None] = None,
        default_database: Union[Path, str, None] = None,
    ) -> None:
        """
        Load the database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        if user_database is None:
            user_database = self._USER_DATABASE
        else:
            user_database = Path(user_database)
        if default_database is None:
            default_database = self._DEFAULT_DATABASE
        else:
            default_database = Path(default_database)

        if user_database.exists():
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
            for alt in v["alternatives"]:
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
        with open(self._USER_DATABASE, "w") as f:
            json.dump(self._data, f)


class AtomsDatabaseError(Error):
    """This class handles the exceptions related to AtomsDatabase"""

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

    _DEFAULT_DATABASE = Path(__file__).parent / "atoms.json"

    # The user path
    _USER_DATABASE = PLATFORM.application_directory() / "atoms.json"

    # The python types supported by the database
    _TYPES = {"str": str, "int": int, "float": float, "list": list}

    def __init__(self):
        """
        Constructor
        """
        self._properties = {}
        self._atoms_by_atomic_number = {num: [] for num in range(140)}

        super().__init__()

    def __contains__(self, element: str) -> bool:
        """
        Return True if the database contains a given element.

        :param element: the name of the element to search in the database
        :type element: str

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
            raise AtomsDatabaseError(
                f"The element {item} is not registered in the database."
            )

    def _load(self, user_database: str = None, default_database: str = None) -> None:
        """
        Load the atom database. This method should never be called elsewhere than __init__ or unit testing.

        :param user_database: The path to the user-defined database. The default path is used by default.
        :type user_database: str or None

        :param default_database: The path to the default MDANSE atom database. The default path is used by default.
        :type default_database: str or None
        """
        super()._load(user_database, default_database)

        self._properties = self._data["properties"]
        self._data = self._data["atoms"]

        try:
            number_of_protons = self.get_property("proton")
        except AtomsDatabaseError:
            pass
        else:
            for atom in self.atoms:
                protons = int(number_of_protons[atom])
                self._atoms_by_atomic_number[protons].append(atom)

    def add_atom(self, atom: str) -> None:
        """
        Add a new element to the atoms database. The data for this atom will be empty and will not be saved until the
        :meth: `save()` method is called. If the atom already exists, an exception is raised.

        :param atom: the name of the element to add
        :type atom: str
        """

        if atom in self._data:
            raise AtomsDatabaseError(
                f"The atom {atom} is already stored in the database"
            )

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
            raise AtomsDatabaseError(
                f"The property {pname} is already registered in the database."
            )

        if ptype not in AtomsDatabase._TYPES:
            raise AtomsDatabaseError(f"The property type {ptype} is unknown")

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
            raise AtomsDatabaseError(f"The atom {atom} is unknown")

        # The isotopes are searched according to |symbol| property
        symbol = self._data[atom]["symbol"]

        return [
            iname for iname, props in self._data.items() if props["symbol"] == symbol
        ]

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
            raise AtomsDatabaseError(
                f"The property {pname} is not registered in the database"
            )

        ptype = AtomsDatabase._TYPES[self._properties[pname]]

        return {
            element: properties.get(pname, ptype())
            for element, properties in self._data.items()
        }

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
            raise AtomsDatabaseError(f"The atom {atom} is unknown")

        if pname not in self._properties:
            raise AtomsDatabaseError(
                f"The property {pname} is not registered in the database"
            )

        ptype = self._properties[pname]
        ptype = AtomsDatabase._TYPES[ptype]

        return self._data[atom].get(pname, ptype())

    def get_values_for_multiple_atoms(
        self, atoms: list[str], prop: str
    ) -> list[Union[str, int, float, list]]:
        """
        Retrieves the values of a given property for multiple atoms efficiently. The atoms may (and, for maximum
        efficiency, should) repeat.

        :param atoms: list of atom names for which the value of the given property is to be retrieved
        :type atoms: list

        :param prop: the property whose value is to be retrieved
        :type prop: str

        :return: list of values of the given property for the provided atoms
        :rtype: list
        """
        unique_atoms = set(atoms)

        if not all(atom in self._data for atom in atoms):
            raise AtomsDatabaseError(
                f"One or more of the provided atoms {atoms} are unknown"
            )

        if prop not in self._properties:
            raise AtomsDatabaseError(
                f"The property {prop} is not registered in the database"
            )

        values = {name: self._data[name][prop] for name in unique_atoms}
        return [values[atom] for atom in atoms]

    def set_value(
        self, atom: str, pname: str, value: Union[str, int, float, list]
    ) -> None:
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
            raise AtomsDatabaseError(f"The element {atom} is unknown")

        if pname not in self._properties:
            raise AtomsDatabaseError(
                f"The property {pname} is not registered in the database"
            )

        try:
            self._data[atom][pname] = AtomsDatabase._TYPES[self._properties[pname]](
                value
            )
        except ValueError:
            raise AtomsDatabaseError(
                f"Can not coerce {value} to {self._properties[pname]} type"
            )

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

        :param atom: the name of the atom whose information is to be returned
        :type atom: str

        :return: the information about a selected atom
        :rype: str
        """

        # A delimiter line.
        delimiter = "-" * 70
        tab_fmt = " {:<20}{!s:>50}"

        info = [
            delimiter,
            f"{atom:^70}",
            tab_fmt.format("property", "value"),
            delimiter,
        ]

        # The values for all element's properties
        for pname in sorted(self._properties):
            info.append(tab_fmt.format(pname, self._data[atom].get(pname, None)))

        info.append(delimiter)
        info = "\n".join(info)

        return info

    def match_numeric_property(
        self, pname: str, value: Union[int, float], tolerance: float = 0.0
    ) -> list[str]:
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
            if self._properties[pname] not in ["int", "float"]:
                raise AtomsDatabaseError(
                    f'The provided property must be numeric, but "{pname}" has type '
                    f"{self._properties[pname]}."
                )
        except KeyError:
            raise AtomsDatabaseError(
                f"The property {pname} is not registered in the database"
            )

        tolerance = abs(tolerance)
        try:
            return [
                atom
                for atom, properties in self._data.items()
                if abs(properties.get(pname, 0) - value) <= tolerance
            ]
        except TypeError:
            raise AtomsDatabaseError(
                f"The provided value must be a numeric type, but {value} was provided, which is of"
                f" type {type(value)}. If you are sure that {value} is numeric, then your database"
                f" might be corrupt."
            )

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
        return [
            pname
            for pname, prop in self._properties.items()
            if prop in ["int", "float"]
        ]

    def _reset(self) -> None:
        """
        Reset the atom database
        """

        self._data.clear()

        self._properties.clear()

    def save(self) -> None:
        """
        Save a copy of the atom database to MDANSE application directory. This database will then be used in the
        future. If the user database already exists, calling this function will overwrite it.
        """

        d = {"properties": self._properties, "atoms": self._data}

        with open(AtomsDatabase._USER_DATABASE, "w") as fout:
            json.dump(d, fout)

    def get_atom_property(self, symbol: str, property: str) -> Union[int, float, str]:
        """Faster access to the atom property as it avoids the deepcopy
        in __getitem__.

        Parameters
        ----------
        symbol : str
            Symbol of the atom.
        property : str
            Property of the atoms to get.

        Returns
        -------
        Union[int, float, str]
            The atom property.
        """
        try:
            return self._data[symbol][property]
        except KeyError:
            if property == "dummy":
                if symbol == "Du":
                    return 1
                if self._data[symbol]["element"] == "dummy":
                    return 1
                return 0
            return None

    def get_property_dict(self, symbol: str) -> Dict[str, Any]:
        """Faster access to the atom property as it avoids the deepcopy
        in __getitem__.

        Parameters
        ----------
        symbol : str
            Symbol of the atom.
        property : str
            Property of the atoms to get.

        Returns
        -------
        Union[int, float, str]
            The atom property.
        """
        return {
            property_name: self.get_value(symbol, property_name)
            for property_name in self.properties
        }


if __name__ == "__main__":
    from MDANSE.Chemistry import ATOMS_DATABASE

    print(ATOMS_DATABASE.numeric_properties)
